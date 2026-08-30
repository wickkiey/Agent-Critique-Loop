"""Demo entrypoint: runs the critique loop on a sample task and writes a timestamped JSON trace."""

import json
from datetime import datetime
from pathlib import Path

from critique_loop import CritiqueLoop

TASK = "Explain why the sky appears blue and under what conditions it can appear a different color."
RUNS_DIR = Path(__file__).parent / "runs"

if __name__ == "__main__":
    loop = CritiqueLoop()
    result = loop.run(TASK)

    print(f"Consensus reached: {result.consensus_reached} (iterations used: {result.iterations_used})")
    print("Final answer:\n", result.final_answer)

    RUNS_DIR.mkdir(exist_ok=True)
    run_file = RUNS_DIR / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    run_file.write_text(json.dumps(result.model_dump(), indent=2, default=str), encoding="utf-8")
    print(f"Trace written to {run_file}")
