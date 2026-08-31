# Agent Critique Loop

An open-source MVP for validating AI-generated work through structured multi-agent debate. Two agents independently solve a task, critique each other's reasoning, revise their responses, and stop when they reach consensus or exhaust the configured iteration limit.

Built to make agent behavior inspectable: every run produces a complete, timestamped JSON trace for debugging, comparison, and evaluation.

<!-- DEMO VIDEO: Replace this comment with a hosted video link or embed.
<a href="https://www.youtube.com/watch?v=YOUR_VIDEO_ID">
	<img src="docs/demo-thumbnail.png" alt="Watch the Agent Critique Loop demo" width="720">
</a>
-->

## What it does

- Runs two configurable agents against a shared task and optional file context.
- Produces independent initial solutions, reciprocal critiques, and refinements.
- Evaluates correctness, missing information, contradictions, evidence, and confidence.
- Stops on agreement or a maximum iteration count.
- Streams the run live in a Streamlit UI and saves complete traces as JSON.
- Includes equivalent implementations using `pydantic-ai` and AutoGen for side-by-side comparison.
- Provides built-in web search and local file-search tools; no search API key is required.

## Demo

**Video placeholder:** Add a short screen recording showing task entry, the live critique loop, consensus, and the exported trace. Replace the commented block above with the final YouTube, Loom, or self-hosted video link.

## Architecture

```text
Task + optional context
					|
		 +----+----+
		 |         |
 Agent A     Agent B
		 |         |
 Initial solutions
					|
	 Reciprocal critiques
					|
			 Revisions
					|
	Consensus or iteration limit
					|
 Final answer + JSON execution trace
```

## Prerequisites

- Python 3.10 or newer.
- [Ollama](https://ollama.com/) running locally.
- An Ollama chat model. The default is `qwen3:8b`.

Pull and start the default model:

```powershell
ollama pull qwen3:8b
ollama serve
```

`ollama serve` is unnecessary when the Ollama desktop application is already running. Confirm the model is available with `ollama list`.

## Quick start

From the repository root, the bundled PowerShell script creates `.venv`, installs every dependency, and runs a sample with both implementations:

```powershell
.\run.ps1
```

## Run the UI

The Streamlit app is the primary MVP experience. It lets you choose a framework, select separate models for Agent A and Agent B, attach `.txt`, `.md`, `.py`, or `.json` context files, and follow each event live.

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Then open the local URL printed by Streamlit, usually `http://localhost:8501`.

## Manual installation

Use this when you prefer not to run `run.ps1`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r pydantic\requirements.txt
python -m pip install -r autogen\requirements.txt
```

If PowerShell prevents activation, run `Set-ExecutionPolicy -Scope Process Bypass` for the current shell, then activate again. You can also use `conda activate torchenv` instead of a virtual environment.

## Run an implementation directly

Each backend is self-contained and writes a trace to its own `runs/` directory.

```powershell
Set-Location pydantic
..\.venv\Scripts\python.exe main.py
```

```powershell
Set-Location autogen
..\.venv\Scripts\python.exe main.py
```

For programmatic or scripted use, each implementation also exposes `cli_run.py`, which emits live `EVENT:` and final `RESULT:` JSON records on standard output.

## Project layout

```text
app.py              Streamlit interface for interactive runs
run.ps1             Bootstrap dependencies and run both demos
pydantic/           pydantic-ai implementation
autogen/            AutoGen implementation
requirement.md      MVP scope and critique-loop flow
*/runs/             Timestamped execution traces
```

## Configuration

Both implementations use the same defaults in their `config.py` files:

| Setting | Default |
| --- | --- |
| Model for Agent A / B | `qwen3:8b` |
| Ollama endpoint | `http://localhost:11434/v1` |
| Maximum critique iterations | `3` |
| Agreement threshold | `0.8` |
| Timeout | `120` seconds |
| Token budget | `8000` |

The UI exposes model choice and maximum iterations. For other settings, edit `pydantic/config.py` or `autogen/config.py`.

## Execution traces

Every completed run is saved as `runs/run_<timestamp>.json` in the selected backend folder. A trace contains:

- Initial solutions and confidence scores.
- Structured critiques, including agreement, correctness, gaps, contradictions, and evidence.
- Revisions, tool calls, and final consensus state.

These files are intentionally kept so you can compare prompts, models, and critique outcomes over time.

## Frameworks

| Directory | Framework | Model integration |
| --- | --- | --- |
| [`pydantic/`](pydantic/) | [pydantic-ai](https://ai.pydantic.dev/) | OpenAI-compatible Ollama endpoint |
| [`autogen/`](autogen/) | [AutoGen](https://microsoft.github.io/autogen/) | OpenAI-compatible Ollama endpoint |

See the implementation-specific READMEs for details: [`pydantic/README.md`](pydantic/README.md) and [`autogen/README.md`](autogen/README.md).

## MVP status

This project is intentionally an MVP. It is suited to local experimentation, evaluating critique patterns, and comparing agent frameworks. Production work should add authentication, durable run storage, queueing, observability, stronger evaluator policies, and model/provider configuration management.

## Contributing

Issues and pull requests are welcome. Useful contributions include evaluator strategies, additional providers, trace viewers, test coverage, and documented benchmark tasks.
