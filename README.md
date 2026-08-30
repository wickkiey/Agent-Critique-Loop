# Agent-Critique-Loop

MVP of the two-agent critique / refine / consensus loop described in [requirement.md](requirement.md),
implemented twice with different agent frameworks so they can be compared side by side. Both talk to a
local Ollama model (`qwen3:8b`) through its OpenAI-compatible endpoint, via the OpenAI SDK.

- [`pydantic/`](pydantic/) — built with `pydantic-ai`
- [`autogen/`](autogen/) — built with `autogen-agentchat`

Each folder is a self-contained project with its own `requirements.txt`, `README.md`, and `main.py` demo.

## Prerequisites

- Conda env `torchenv` (use `conda activate torchenv` before installing/running either implementation)
- Ollama running locally with the `qwen3:8b` model pulled (`ollama pull qwen3:8b`)

## Quick start

`run.ps1` creates a local `.venv` (if it doesn't already exist), installs both implementations'
dependencies into it, and runs a sample critique with each agent:

```powershell
.\run.ps1
```

Each run writes a timestamped trace to `pydantic/runs/run_<timestamp>.json` and
`autogen/runs/run_<timestamp>.json` (never overwritten) so you can compare past runs later.

See each subfolder's README for install/run instructions.
