from __future__ import annotations

from pathlib import Path

from dissertation.models.schemas import Epic, RequirementSet


def to_markdown(epic: Epic, req: RequirementSet) -> str:
    lines = []
    lines.append(f"# Requirement Set — {req.mode}")
    lines.append("")
    lines.append(f"## Epic {epic.epic_id}")
    lines.append(epic.text.strip())
    lines.append("")

    if epic.constraints:
        lines.append("### Constraints")
        for c in epic.constraints:
            lines.append(f"- {c}")
        lines.append("")

    lines.append("## User Stories")
    for s in req.stories:
        lines.append(f"### {s.story_id}")
        lines.append(s.story_text)
        if s.assumptions:
            lines.append("")
            lines.append("**Assumptions**")
            for a in s.assumptions:
                lines.append(f"- {a}")
        if s.open_questions:
            lines.append("")
            lines.append("**Open questions**")
            for q in s.open_questions:
                lines.append(f"- {q}")
        lines.append("")

    lines.append("## Acceptance Criteria (Gherkin)")
    sc_by_story = {}
    for sc in req.scenarios:
        sc_by_story.setdefault(sc.story_id, []).append(sc)

    for story_id, scenarios in sc_by_story.items():
        lines.append(f"### {story_id}")
        for sc in scenarios:
            lines.append(f"#### {sc.scenario_id}: {sc.title}")
            for g in sc.given:
                lines.append(f"- GIVEN {g}")
            for w in sc.when:
                lines.append(f"- WHEN {w}")
            for t in sc.then:
                lines.append(f"- THEN {t}")
            lines.append("")

    lines.append("## Quality Summary")
    for qr in req.quality_reports:
        inv = qr.invest
        lines.append(
            f"- **{qr.story_id}** — Overall: {qr.overall_score:.2f} | "
            f"INVEST(I,N,V,E,S,T)=({inv.I},{inv.N},{inv.V},{inv.E},{inv.S},{inv.T}) | "
            f"Gherkin valid: {qr.gherkin_valid}"
        )
    lines.append("")
    return "\n".join(lines)


def export_bundle(epic: Epic, req: RequirementSet, out_dir: str | Path) -> Path:
    out_dir = Path(out_dir)
    run_folder = out_dir / epic.epic_id / req.mode / req.run_metadata.run_id
    run_folder.mkdir(parents=True, exist_ok=True)

    (run_folder / "epic.json").write_text(epic.model_dump_json(indent=2), encoding="utf-8")
    (run_folder / "requirement_set.json").write_text(
        req.model_dump_json(indent=2), encoding="utf-8"
    )
    (run_folder / "requirements.md").write_text(to_markdown(epic, req), encoding="utf-8")

    rows = ["story_id,overall_score,I,N,V,E,S,T,gherkin_valid"]
    for qr in req.quality_reports:
        inv = qr.invest
        rows.append(
            f"{qr.story_id},{qr.overall_score:.2f},{inv.I},{inv.N},{inv.V},{inv.E},{inv.S},{inv.T},{qr.gherkin_valid}"
        )
    (run_folder / "summary.csv").write_text("\n".join(rows), encoding="utf-8")

    return run_folder


def get_run_folder(epic_id: str, mode: str, run_id: str, out_dir: str | Path) -> Path:
    out_dir = Path(out_dir)
    run_folder = out_dir / epic_id / mode / run_id
    run_folder.mkdir(parents=True, exist_ok=True)
    return run_folder
