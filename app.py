"""Streamlit UI for the Agent-Critique-Loop: pick a framework, submit a task, watch the critique loop."""

import subprocess
import sys
import json
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parent
FRAMEWORKS = {
    "pydantic-ai": ROOT / "pydantic",
    "AutoGen": ROOT / "autogen",
}
AGENT_COLOR = {"AgentA": "#1f6feb22", "AgentB": "#da363322"}
AGENT_BORDER = {"AgentA": "#1f6feb", "AgentB": "#da3633"}
STEP_LABEL = {"initial_solution": "Initial Solution", "critique": "Critique", "revision": "Revision"}

st.set_page_config(page_title="Agent Critique Loop", layout="wide")
st.title("Agent Critique Loop")
st.caption("Two agents independently solve, critique each other, and refine until consensus (or max iterations).")

with st.sidebar:
    st.header("Run configuration")
    framework = st.selectbox("Framework", list(FRAMEWORKS.keys()))
    task_text = st.text_area(
        "Task",
        value="Explain why the sky appears blue and under what conditions it can appear a different color.",
        height=140,
    )
    uploaded_files = st.file_uploader(
        "Optional context files (.txt, .md, .py, .json)",
        type=["txt", "md", "py", "json"],
        accept_multiple_files=True,
    )
    run_clicked = st.button("Run critique loop", type="primary")


def build_task(task: str, files: list) -> str:
    if not files:
        return task
    parts = [task, "\nAdditional context from uploaded files:"]
    for f in files:
        content = f.read().decode("utf-8", errors="ignore")
        parts.append(f"\n--- {f.name} ---\n{content}")
    return "\n".join(parts)


def run_critique_loop(framework_dir: Path, task: str) -> dict:
    script = framework_dir / "cli_run.py"
    proc = subprocess.run(
        [sys.executable, str(script), task],
        capture_output=True,
        text=True,
        timeout=600,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-4000:] or "Unknown error running critique loop.")
    trace_line = next(line for line in proc.stdout.splitlines() if line.startswith("TRACE_PATH:"))
    trace_path = Path(trace_line.removeprefix("TRACE_PATH:"))
    return json.loads(trace_path.read_text(encoding="utf-8"))


def render_event(event: dict):
    step = STEP_LABEL.get(event["step"], event["step"])
    color = AGENT_COLOR.get(event["agent"], "#88888822")
    border = AGENT_BORDER.get(event["agent"], "#888888")
    payload = event["payload"]
    body = "\n".join(f"**{k}:** {v}" for k, v in payload.items())
    st.markdown(
        f"""<div style="background:{color};border-left:4px solid {border};
        border-radius:6px;padding:10px 14px;margin-bottom:10px;">
        <div style="font-weight:600;margin-bottom:4px;">Iteration {event['iteration']} · {step}</div>
        <div style="font-size:0.9em;white-space:pre-wrap;">{body}</div>
        </div>""",
        unsafe_allow_html=True,
    )


if run_clicked:
    full_task = build_task(task_text, uploaded_files or [])
    with st.spinner(f"Running {framework} critique loop..."):
        try:
            result = run_critique_loop(FRAMEWORKS[framework], full_task)
        except Exception as exc:
            st.error(f"Run failed: {exc}")
            st.stop()

    col_a, col_b = st.columns(2)
    col_a.subheader("🔵 Agent A")
    col_b.subheader("🔴 Agent B")

    for event in result["trace"]:
        target_col = col_a if event["agent"] == "AgentA" else col_b
        with target_col:
            render_event(event)

    st.divider()
    st.subheader("Final Result")
    m1, m2, m3 = st.columns(3)
    m1.metric("Consensus reached", "Yes" if result["consensus_reached"] else "No")
    m2.metric("Iterations used", result["iterations_used"])
    m3.metric("Framework", framework)
    st.markdown(result["final_answer"])
else:
    st.info("Configure a task in the sidebar and click **Run critique loop** to start.")
