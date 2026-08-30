# Critique Agent — pydantic-ai implementation

Two-agent critique / refine / consensus loop built with [`pydantic-ai`](https://ai.pydantic.dev), talking
to a local Ollama model (`qwen3:8b`) through its OpenAI-compatible API.

## Setup

```powershell
conda activate torchenv
ollama list                 # confirm qwen3:8b is present, otherwise: ollama pull qwen3:8b
pip install -r requirements.txt
```

## Run

```powershell
python main.py
```

Prints the final answer and consensus status, and writes a timestamped trace file to
`runs/run_<YYYYMMDD_HHMMSS>.json` with the full execution trace (initial solutions,
critiques, revisions) so past runs can be compared later.

## Files

- `config.py` — model/loop settings (max iterations, agreement threshold, timeout, token budget)
- `models.py` — `Solution`, `Critique`, `TraceEvent`, `RunResult` pydantic models
- `tools.py` — stub `knowledge_lookup` tool used as evidence source
- `agents.py` — wires `pydantic_ai.Agent` to Ollama via `OpenAIProvider`
- `critique_loop.py` — orchestrates the critique/refine/consensus loop
- `main.py` — demo entrypoint
