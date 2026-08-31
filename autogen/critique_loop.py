"""Two-agent critique -> refine -> consensus loop, orchestrated with AutoGen AgentChat agents."""

import asyncio
import time
from typing import Callable

from autogen_agentchat.base import TaskResult

from agents import build_model_client, create_agent
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


def _usage_tokens(result: TaskResult) -> int:
    total = 0
    for message in result.messages:
        usage = getattr(message, "models_usage", None)
        if usage:
            total += usage.prompt_tokens + usage.completion_tokens
    return total


def _tool_calls(result: TaskResult) -> list[dict]:
    """Pair FunctionCall requests with their FunctionExecutionResults into readable log entries."""
    calls: dict[str, dict] = {}
    for message in result.messages:
        content = getattr(message, "content", None)
        if not isinstance(content, list):
            continue
        for item in content:
            call_id = getattr(item, "id", None) or getattr(item, "call_id", "")
            if hasattr(item, "arguments"):
                calls[call_id] = {"name": getattr(item, "name", ""), "args": item.arguments, "result": ""}
            elif hasattr(item, "call_id"):
                entry = calls.setdefault(call_id, {"name": getattr(item, "name", ""), "args": "", "result": ""})
                entry["result"] = str(getattr(item, "content", ""))
    return list(calls.values())


class CritiqueLoop:
    def __init__(self, config: Config | None = None, on_event: Callable[[TraceEvent], None] | None = None):
        self.config = config or Config()
        self.on_event = on_event
        client_a = build_model_client(self.config, self.config.model_a)
        client_b = build_model_client(self.config, self.config.model_b)
        self.solver_a = create_agent(client_a, "AgentA", SOLVER_SYSTEM.format(name="AgentA"), Solution, with_tools=True)
        self.solver_b = create_agent(client_b, "AgentB", SOLVER_SYSTEM.format(name="AgentB"), Solution, with_tools=True)
        self.critic_a = create_agent(client_a, "AgentA", CRITIC_SYSTEM.format(name="AgentA"), Critique)
        self.critic_b = create_agent(client_b, "AgentB", CRITIC_SYSTEM.format(name="AgentB"), Critique)

    def run(self, task: str) -> RunResult:
        return asyncio.run(self._run(task))

    def _trace(self, trace: list[TraceEvent], step: str, agent: str, iteration: int, output, tools: list[dict]):
        event = TraceEvent(
            step=step,
            agent=agent,
            iteration=iteration,
            payload=output.model_dump(),
            tools=tools,
            model=self.config.model_a if agent == "AgentA" else self.config.model_b,
        )
        trace.append(event)
        if self.on_event:
            self.on_event(event)

    async def _ask(self, agent, text: str):
        result = await agent.run(task=text)
        return result.messages[-1].content, _usage_tokens(result), _tool_calls(result)

    async def _run(self, task: str) -> RunResult:
        trace: list[TraceEvent] = []
        start = time.monotonic()
        tokens_used = 0

        solution_a, used, tools = await self._ask(self.solver_a, task)
        tokens_used += used
        self._trace(trace, "initial_solution", "AgentA", 0, solution_a, tools)
        solution_b, used, tools = await self._ask(self.solver_b, task)
        tokens_used += used
        self._trace(trace, "initial_solution", "AgentB", 0, solution_b, tools)

        consensus = False
        iteration = 0
        while iteration < self.config.max_iterations:
            if time.monotonic() - start > self.config.timeout_seconds:
                break
            if tokens_used > self.config.token_budget:
                break
            iteration += 1

            critique_a_on_b, used, tools = await self._ask(
                self.critic_a, f"Task: {task}\nSolution to critique:\n{solution_b.content}"
            )
            tokens_used += used
            self._trace(trace, "critique", "AgentA", iteration, critique_a_on_b, tools)
            critique_b_on_a, used, tools = await self._ask(
                self.critic_b, f"Task: {task}\nSolution to critique:\n{solution_a.content}"
            )
            tokens_used += used
            self._trace(trace, "critique", "AgentB", iteration, critique_b_on_a, tools)

            if (
                critique_a_on_b.agree
                and critique_b_on_a.agree
                and critique_a_on_b.confidence >= self.config.agreement_threshold
                and critique_b_on_a.confidence >= self.config.agreement_threshold
            ):
                consensus = True
                break

            solution_a, used, tools = await self._ask(
                self.solver_a,
                f"Task: {task}\nYour previous answer:\n{solution_a.content}\n"
                f"Critique received:\n{critique_b_on_a.model_dump_json()}\nRevise your answer.",
            )
            tokens_used += used
            self._trace(trace, "revision", "AgentA", iteration, solution_a, tools)
            solution_b, used, tools = await self._ask(
                self.solver_b,
                f"Task: {task}\nYour previous answer:\n{solution_b.content}\n"
                f"Critique received:\n{critique_a_on_b.model_dump_json()}\nRevise your answer.",
            )
            tokens_used += used
            self._trace(trace, "revision", "AgentB", iteration, solution_b, tools)

        final = solution_a if solution_a.confidence >= solution_b.confidence else solution_b
        return RunResult(
            final_answer=final.content,
            consensus_reached=consensus,
            iterations_used=iteration,
            trace=trace,
        )
