"""CLI entrypoint used by the Streamlit UI: streams trace events as NDJSON and writes a run file.

Runs isolated as its own subprocess so its `config`/`models`/`agents` modules never clash with pydantic/'s.
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

from config import Config
from critique_loop import CritiqueLoop

RUNS_DIR = Path(__file__).parent / "runs"


def emit(kind: str, data: dict):
    """One JSON object per line on stdout, flushed so the UI can render it immediately."""
    print(f"{kind}:{json.dumps(data, default=str)}", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("task")
    parser.add_argument("--model-a", default=Config().model_a)
    parser.add_argument("--model-b", default=Config().model_b)
    parser.add_argument("--max-iterations", type=int, default=Config().max_iterations)
    args = parser.parse_args()

    config = Config(model_a=args.model_a, model_b=args.model_b, max_iterations=args.max_iterations)
    loop = CritiqueLoop(config, on_event=lambda event: emit("EVENT", event.model_dump()))
    result = loop.run(args.task)

    RUNS_DIR.mkdir(exist_ok=True)
    run_file = RUNS_DIR / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    run_file.write_text(json.dumps(result.model_dump(), indent=2, default=str), encoding="utf-8")

    emit(
        "RESULT",
        {
            "final_answer": result.final_answer,
            "consensus_reached": result.consensus_reached,
            "iterations_used": result.iterations_used,
            "trace_path": str(run_file.resolve()),
        },
    )


if __name__ == "__main__":
    main()
