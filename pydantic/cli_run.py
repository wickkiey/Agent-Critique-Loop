"""CLI entrypoint used by the Streamlit UI: runs one critique loop and writes a timestamped trace file.

Runs isolated as its own subprocess so its `config`/`models`/`agents` modules never clash with autogen/'s.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

from critique_loop import CritiqueLoop

RUNS_DIR = Path(__file__).parent / "runs"

if __name__ == "__main__":
    task = sys.argv[1]

    loop = CritiqueLoop()
    result = loop.run(task)

    RUNS_DIR.mkdir(exist_ok=True)
    run_file = RUNS_DIR / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    run_file.write_text(json.dumps(result.model_dump(), indent=2, default=str), encoding="utf-8")

    # Last stdout line is parsed by the caller to locate the trace file.
    print(f"TRACE_PATH:{run_file.resolve()}")
