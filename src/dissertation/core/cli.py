from __future__ import annotations

import argparse
from pathlib import Path

from dissertation.core.exporter import export_bundle
from dissertation.core.orchestrator import run_agentic, run_llm_baseline
from dissertation.models.schemas import Epic


def main() -> None:
    parser = argparse.ArgumentParser(prog="dissertation")
    parser.add_argument("--epic", required=False, help="Path to epic JSON file")
    parser.add_argument("--out", default="outputs", help="Output directory")
    parser.add_argument("--version", action="store_true", help="Print version and exit")

    parser.add_argument("--mode", choices=["llm_baseline", "agentic"], default="llm_baseline")
    parser.add_argument("--openai", action="store_true", help="Use OpenAI for llm_baseline mode")
    parser.add_argument("--model", default=None, help="Model override (else uses OPENAI_MODEL)")
    parser.add_argument("--temperature", type=float, default=0.2, help="Temperature (default 0.2)")

    # Agentic tuning (safe defaults)
    parser.add_argument("--max-iters", type=int, default=3)
    parser.add_argument("--target-score", type=float, default=4.2)
    parser.add_argument(
        "--force-min-iters",
        type=int,
        default=1,
        help="Force at least N critique/refine iterations in agentic mode (default 1)",
    )

    args = parser.parse_args()

    if args.version:
        print("msc-dissertation 0.1.0")
        return

    if not args.epic:
        raise SystemExit("❌ Please provide --epic path/to/epic.json")

    epic_path = Path(args.epic)
    out_dir = Path(args.out)
    epic = Epic.model_validate_json(epic_path.read_text(encoding="utf-8"))

    if args.mode == "llm_baseline":
        req = run_llm_baseline(
            epic,
            force_openai=bool(args.openai),
            model_name=args.model,
            temperature=args.temperature,
        )
    else:
        req = run_agentic(
            epic,
            model_name=args.model,
            temperature=args.temperature,
            max_iters=args.max_iters,
            target_score=args.target_score,
            out_dir=str(out_dir),
            force_min_iters=args.force_min_iters,
        )

    folder = export_bundle(epic, req, out_dir)
    print(f"✅ Exported run bundle to: {folder}")
    print(
        f"ℹ️ Mode: {req.mode} | Generator used: {req.run_metadata.model_name} | Iteration: {req.run_metadata.iteration}"
    )
