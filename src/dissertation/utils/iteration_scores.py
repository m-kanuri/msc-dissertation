from __future__ import annotations

from pathlib import Path


def write_iteration_scores(run_folder: Path, rows: list[dict]) -> None:
    header = ["iteration", "avg_score", "hard_ok", "gherkin_ok", "trace_ok", "edits_count"]
    lines = [",".join(header)]
    for r in rows:
        vals = []
        for h in header:
            v = r.get(h, "")
            if isinstance(v, bool):
                v = "True" if v else "False"
            vals.append(str(v))
        lines.append(",".join(vals))
    # Ensure trailing newline
    (run_folder / "iteration_scores.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
