"""Two-agent critique -> refine -> consensus loop, orchestrated with pydantic-ai agents."""

import time
from typing import Callable

from agents import create_agent
from config import Config
from models import Critique, RunResult, Solution, TraceEvent

SOLVER_SYSTEM = (
    "You are {name}, an independent problem solver. Use the web_search tool for external facts and "
    "the file_search tool to look for supporting information in local project files, when useful. "
    "Answer the task directly and concisely."
)
CRITIC_SYSTEM = (
    "You are {name}, a rigorous critic. Evaluate the given solution for correctness, "
    "missing information, contradictions and evidence. Be specific and honest about confidence."
)


def _tool_calls(result) -> list[dict]:
    """Pair up tool-call and tool-return parts from a pydantic-ai run into readable log entries."""
    calls: dict[str, dict] = {}
    for message in result.all_messages():
        for part in getattr(message, "parts", []):
            kind = getattr(part, "part_kind", "")
            tool_name = getattr(part, "tool_name", "") or ""
            if tool_name == "final_result":  # structured-output plumbing, not a real tool
                continue
            call_id = getattr(part, "tool_call_id", "") or tool_name
            if kind == "tool-call":
                calls[call_id] = {"name": tool_name, "args": str(getattr(part, "args", "")), "result": ""}
            elif kind == "tool-return":
                entry = calls.setdefault(call_id, {"name": tool_name, "args": "", "result": ""})
                entry["result"] = str(getattr(part, "content", ""))
    return list(calls.values())


class CritiqueLoop:
    def __init__(self, config: Config | None = None, on_event: Callable[[TraceEvent], None] | None = None):
        self.config = config or Config()
        self.on_event = on_event
        model_a, model_b = self.config.model_a, self.config.model_b
        self.solver_a = create_agent(self.config, "AgentA", SOLVER_SYSTEM.format(name="AgentA"), Solution, model_a)
        self.solver_b = create_agent(self.config, "AgentB", SOLVER_SYSTEM.format(name="AgentB"), Solution, model_b)
        self.critic_a = create_agent(self.config, "AgentA", CRITIC_SYSTEM.format(name="AgentA"), Critique, model_a)
        self.critic_b = create_agent(self.config, "AgentB", CRITIC_SYSTEM.format(name="AgentB"), Critique, model_b)

    def _trace(self, trace: list[TraceEvent], step: str, agent: str, iteration: int, result):
        event = TraceEvent(
            step=step,
            agent=agent,
            iteration=iteration,
            payload=result.output.model_dump(),
            tools=_tool_calls(result),
            tokens=result.usage.total_tokens,
            model=self.config.model_a if agent == "AgentA" else self.config.model_b,
        )
        trace.append(event)
        if self.on_event:
            self.on_event(event)

    def run(self, task: str) -> RunResult:
        trace: list[TraceEvent] = []
        start = time.monotonic()
        tokens_used = 0

        result_a = self.solver_a.run_sync(task)
        self._trace(trace, "initial_solution", "AgentA", 0, result_a)
        result_b = self.solver_b.run_sync(task)
        self._trace(trace, "initial_solution", "AgentB", 0, result_b)
        tokens_used += result_a.usage.total_tokens + result_b.usage.total_tokens
        solution_a, solution_b = result_a.output, result_b.output

        consensus = False
        iteration = 0
        while iteration < self.config.max_iterations:
            if time.monotonic() - start > self.config.timeout_seconds:
                break
            if tokens_used > self.config.token_budget:
                break
            iteration += 1

            critique_a_on_b = self.critic_a.run_sync(f"Task: {task}\nSolution to critique:\n{solution_b.content}")
            self._trace(trace, "critique", "AgentA", iteration, critique_a_on_b)
            critique_b_on_a = self.critic_b.run_sync(f"Task: {task}\nSolution to critique:\n{solution_a.content}")
            self._trace(trace, "critique", "AgentB", iteration, critique_b_on_a)
            tokens_used += critique_a_on_b.usage.total_tokens + critique_b_on_a.usage.total_tokens

            if (
                critique_a_on_b.output.agree
                and critique_b_on_a.output.agree
                and critique_a_on_b.output.confidence >= self.config.agreement_threshold
                and critique_b_on_a.output.confidence >= self.config.agreement_threshold
            ):
                consensus = True
                break

            revise_a = self.solver_a.run_sync(
                f"Task: {task}\nYour previous answer:\n{solution_a.content}\n"
                f"Critique received:\n{critique_b_on_a.output.model_dump_json()}\nRevise your answer."
            )
            self._trace(trace, "revision", "AgentA", iteration, revise_a)
            revise_b = self.solver_b.run_sync(
                f"Task: {task}\nYour previous answer:\n{solution_b.content}\n"
                f"Critique received:\n{critique_a_on_b.output.model_dump_json()}\nRevise your answer."
            )
            self._trace(trace, "revision", "AgentB", iteration, revise_b)
            tokens_used += revise_a.usage.total_tokens + revise_b.usage.total_tokens
            solution_a, solution_b = revise_a.output, revise_b.output

        final = solution_a if solution_a.confidence >= solution_b.confidence else solution_b
        return RunResult(
            final_answer=final.content,
            consensus_reached=consensus,
            iterations_used=iteration,
            trace=trace,
        )
