"""Streamlit UI for the Agent-Critique-Loop: configure models, submit a task, watch the critique loop live."""

import json
import subprocess
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parent
FRAMEWORKS = {
    "pydantic-ai": ROOT / "pydantic",
    "AutoGen": ROOT / "autogen",
}
AGENTS = {
    "AgentA": {"icon": "🔵", "label": "Agent A", "accent": "#1f6feb", "tint": "#1f6feb18"},
    "AgentB": {"icon": "🔴", "label": "Agent B", "accent": "#da3633", "tint": "#da363318"},
}
STEP_LABEL = {"initial_solution": "Initial Solution", "critique": "Critique", "revision": "Revision"}
MODEL_CHOICES = ["qwen3:8b", "qwen3:4b", "llama3.1:8b", "mistral:7b", "phi4", "gemma3:12b", "Custom…"]

st.set_page_config(page_title="Agent Critique Loop", layout="wide")
st.title("Agent Critique Loop")
st.caption("Two agents independently solve, critique each other, and refine until consensus (or max iterations).")


def pick_model(slot: str) -> str:
    choice = st.selectbox("Ollama model", MODEL_CHOICES, key=f"preset_{slot}", label_visibility="collapsed")
    if choice == "Custom…":
        return st.text_input("Custom model name", value="qwen3:8b", key=f"custom_{slot}")
    return choice


with st.sidebar:
    st.header("Run configuration")
    framework = st.selectbox("Framework", list(FRAMEWORKS.keys()))
    max_iterations = st.slider("Max critique iterations", min_value=1, max_value=8, value=3)

    st.subheader("🔵 Agent A model")
    model_a = pick_model("a")

    st.subheader("🔴 Agent B model")
    model_b = pick_model("b")

    st.subheader("Task")
    task_text = st.text_area(
        "Task",
        value="Explain why the sky appears blue and under what conditions it can appear a different color.",
        height=140,
        label_visibility="collapsed",
    )
    uploaded_files = st.file_uploader(
        "Optional context files (.txt, .md, .py, .json)",
        type=["txt", "md", "py", "json"],
        accept_multiple_files=True,
    )
    run_clicked = st.button("Run critique loop", type="primary", width="stretch")


def build_task(task: str, files: list) -> str:
    if not files:
        return task
    parts = [task, "\nAdditional context from uploaded files:"]
    for f in files:
        content = f.read().decode("utf-8", errors="ignore")
        parts.append(f"\n--- {f.name} ---\n{content}")
    return "\n".join(parts)


def stream_critique_loop(framework_dir: Path, task: str, model_a: str, model_b: str, iterations: int):
    """Yield (kind, data) pairs as the subprocess emits them, so the UI can render events live."""
    cmd = [
        sys.executable,
        "-u",
        str(framework_dir / "cli_run.py"),
        task,
        "--model-a",
        model_a,
        "--model-b",
        model_b,
        "--max-iterations",
        str(iterations),
    ]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    for line in proc.stdout:
        line = line.strip()
        for kind in ("EVENT", "RESULT"):
            if line.startswith(f"{kind}:"):
                yield kind, json.loads(line[len(kind) + 1 :])
                break
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr.read() or "")[-4000:] or "Unknown error running critique loop.")


def header_html(event: dict) -> str:
    meta = AGENTS.get(event["agent"], {"icon": "⚪", "label": event["agent"], "accent": "#888", "tint": "#88888818"})
    step = STEP_LABEL.get(event["step"], event["step"])
    tokens = f" · {event['tokens']} tokens" if event.get("tokens") else ""
    return (
        f"<div style='background:{meta['tint']};border-left:4px solid {meta['accent']};"
        f"border-radius:8px;padding:8px 12px;margin-bottom:8px;'>"
        f"<span style='font-weight:700;color:{meta['accent']};'>{meta['icon']} {meta['label']}</span>"
        f"<span style='opacity:.75;'> · Iteration {event['iteration']} · {step}</span>"
        f"<div style='font-size:.8em;opacity:.6;'>{event.get('model', '')}{tokens}</div>"
        f"</div>"
    )


def render_event(event: dict):
    payload = event["payload"]
    st.html(header_html(event))

    if event["step"] == "critique":
        verdict = "✅ Agrees" if payload.get("agree") else "❌ Disagrees"
        correctness = "correct" if payload.get("correctness") else "incorrect"
        st.markdown(f"**{verdict}** · judged *{correctness}* · confidence `{payload.get('confidence', 0):.2f}`")
        for label, key in (("Missing information", "missing_information"), ("Contradictions", "contradictions")):
            items = payload.get(key) or []
            if items:
                st.markdown(f"**{label}**\n" + "\n".join(f"- {i}" for i in items))
        evidence = payload.get("evidence") or []
        if evidence:
            with st.expander(f"Evidence ({len(evidence)})"):
                st.markdown("\n".join(f"- {e}" for e in evidence))
    else:
        st.markdown(payload.get("content", ""))
        st.caption(f"Confidence: {payload.get('confidence', 0):.2f}")

    tools = event.get("tools") or []
    if tools:
        with st.expander(f"🛠 Tool calls ({len(tools)})"):
            for call in tools:
                st.markdown(f"**{call.get('name', 'tool')}**")
                st.code(str(call.get("args", "")), language="json")
                st.text(str(call.get("result", ""))[:2000] or "(no output)")
    with st.expander("Raw event JSON"):
        st.json(event)


def thinking_html(agent: str) -> str:
    meta = AGENTS.get(agent, {"icon": "⚪", "label": agent, "accent": "#888", "tint": "#88888818"})
    return f"""
<style>
@keyframes acl-bounce {{ 0%, 80%, 100% {{ transform: scale(.5); opacity:.35; }} 40% {{ transform: scale(1); opacity:1; }} }}
@keyframes acl-sweep {{ 0% {{ background-position: -320px 0; }} 100% {{ background-position: 320px 0; }} }}
.acl-think {{ border:1px dashed {meta['accent']}66; background:{meta['tint']}; border-radius:10px; padding:14px 16px; }}
.acl-dot {{ width:9px; height:9px; border-radius:50%; background:{meta['accent']}; display:inline-block;
            margin-right:5px; animation: acl-bounce 1.2s infinite ease-in-out; }}
.acl-bar {{ height:9px; border-radius:5px; margin-top:12px;
            background: linear-gradient(90deg, {meta['accent']}18 25%, {meta['accent']}55 50%, {meta['accent']}18 75%);
            background-size: 320px 100%; animation: acl-sweep 1.3s linear infinite; }}
.acl-bar.short {{ width:60%; }}
</style>
<div class="acl-think">
  <span style="font-weight:700;color:{meta['accent']};">{meta['icon']} {meta['label']}</span>
  <span style="opacity:.7;"> is thinking</span>
  <span style="margin-left:8px;">
    <span class="acl-dot"></span>
    <span class="acl-dot" style="animation-delay:.16s;"></span>
    <span class="acl-dot" style="animation-delay:.32s;"></span>
  </span>
  <div class="acl-bar"></div>
  <div class="acl-bar short"></div>
</div>
"""


if run_clicked:
    full_task = build_task(task_text, uploaded_files or [])
    st.markdown(f"#### 🔵 `{model_a}` &nbsp;&nbsp;↔&nbsp;&nbsp; 🔴 `{model_b}`")
    status = st.status("Starting critique loop...", expanded=False)

    # One persistent column per agent so cards stack independently instead of each pair
    # reserving a full-width row; the spacer offsets Agent B slightly below Agent A.
    left, right = st.columns(2, gap="medium")
    right.html("<div style='height:56px'></div>")
    columns = {"AgentA": left, "AgentB": right}

    next_agent = "AgentA"
    slot = columns[next_agent].empty()
    slot.html(thinking_html(next_agent))
    result = None

    try:
        for kind, data in stream_critique_loop(FRAMEWORKS[framework], full_task, model_a, model_b, max_iterations):
            if kind == "RESULT":
                result = data
                continue
            with slot.container(border=True):
                render_event(data)
            label = AGENTS.get(data["agent"], {}).get("label", data["agent"])
            step = STEP_LABEL.get(data["step"], data["step"])
            status.update(label=f"{label} · iteration {data['iteration']} · {step} done")
            next_agent = "AgentB" if data["agent"] == "AgentA" else "AgentA"
            slot = columns[next_agent].empty()
            slot.html(thinking_html(next_agent))
    except Exception as exc:
        slot.empty()
        status.update(label="Run failed", state="error")
        st.error(f"Run failed: {exc}")
        st.stop()

    slot.empty()
    status.update(label="Critique loop finished", state="complete")

    if result:
        st.divider()
        st.subheader("Final Result")
        m1, m2, m3 = st.columns(3)
        m1.metric("Consensus reached", "Yes" if result["consensus_reached"] else "No")
        m2.metric("Iterations used", result["iterations_used"])
        m3.metric("Framework", framework)
        st.markdown(result["final_answer"])
        st.caption(f"Full trace saved to `{result['trace_path']}`")
else:
    st.info("Configure models and a task in the sidebar, then click **Run critique loop** to start.")
