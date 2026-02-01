from __future__ import annotations

import csv
from pathlib import Path
from dissertation.models.schemas import Epic, RequirementSet


def _gherkin_text_for_story(story_id: str, req: RequirementSet) -> str:
    scenario_ids = req.trace_map.get(story_id, [])
    scenarios = [s for s in req.scenarios if s.scenario_id in scenario_ids]

    blocks: list[str] = []
    for sc in scenarios:

        sc_title = getattr(sc, "title", sc.scenario_id)
        blocks.append(f"Scenario: {sc_title}")

        for g in sc.given:
            blocks.append(f"  Given {g}")
        for w in sc.when:
            blocks.append(f"  When {w}")
        for t in sc.then:
            blocks.append(f"  Then {t}")
        blocks.append("")  # blank line
    return "\n".join(blocks).strip()


def export_jira_csv(
    epic: Epic,
    req: RequirementSet,
    out_path: str | Path,
) -> str:
    """
    Exports a Jira CSV import file:
    - Epic row
    - Story rows linked to epic via 'Epic Link'
    - Scenario rows as Sub-tasks linked to story via 'Parent Summary'
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    epic_name = f"{epic.epic_id} {epic.text[:60]}".strip()

    headers = [
        "Issue Type",
        "Summary",
        "Description",
        "Epic Name",
        "Epic Link",
        "Parent Summary",
    ]

    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()

        # 1) Epic
        w.writerow(
            {
                "Issue Type": "Epic",
                "Summary": epic_name,
                "Description": f"Epic ID: {epic.epic_id}\n\n{epic.text}",
                "Epic Name": epic_name,
                "Epic Link": "",
                "Parent Summary": "",
            }
        )

        # 2) Stories (linked to epic)
        story_summary_by_id: dict[str, str] = {}
        for us in req.stories:
            story_text = us.story_text  # <-- correct field in your schema
            summary = f"{us.story_id} {story_text[:60]}".strip()
            story_summary_by_id[us.story_id] = summary

            desc_parts = [
                story_text,
                "",
            ]
            if getattr(us, "assumptions", None):
                desc_parts.append("Assumptions:")
                desc_parts.extend([f"- {a}" for a in us.assumptions])
                desc_parts.append("")
            if getattr(us, "open_questions", None):
                desc_parts.append("Open Questions:")
                desc_parts.extend([f"- {q}" for q in us.open_questions])
                desc_parts.append("")

            gherkin = _gherkin_text_for_story(us.story_id, req)
            if gherkin:
                desc_parts.append("Acceptance Criteria (Gherkin):")
                desc_parts.append(gherkin)

            w.writerow(
                {
                    "Issue Type": "Story",
                    "Summary": summary,
                    "Description": "\n".join(desc_parts).strip(),
                    "Epic Name": "",
                    "Epic Link": epic_name,
                    "Parent Summary": "",
                }
            )

        # 3) Scenarios as Sub-tasks (parent = story summary)
        # Create one sub-task per scenario and attach under its story via trace_map
        for story_id, scenario_ids in req.trace_map.items():
            parent_summary = story_summary_by_id.get(story_id)
            if not parent_summary:
                continue

            for sc_id in scenario_ids:
                sc = next((x for x in req.scenarios if x.scenario_id == sc_id), None)
                if not sc:
                    continue

                sc_title = getattr(sc, "title", sc.scenario_id)
                sc_summary = f"{sc.scenario_id} {sc_title}".strip()
                sc_desc_lines = [f"Scenario: {sc_title}"]

                for g in sc.given:
                    sc_desc_lines.append(f"Given {g}")
                for w_ in sc.when:
                    sc_desc_lines.append(f"When {w_}")
                for t in sc.then:
                    sc_desc_lines.append(f"Then {t}")

                w.writerow(
                    {
                        "Issue Type": "Sub-task",
                        "Summary": sc_summary,
                        "Description": "\n".join(sc_desc_lines),
                        "Epic Name": "",
                        "Epic Link": "",
                        "Parent Summary": parent_summary,
                    }
                )

    return str(out_path)
