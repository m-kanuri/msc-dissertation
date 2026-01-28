from __future__ import annotations

from dissertation.models.schemas import RequirementSet


def check_trace(req: RequirementSet) -> tuple[bool, list[str]]:
    violations: list[str] = []

    story_ids = [s.story_id for s in req.stories]
    if len(story_ids) != len(set(story_ids)):
        violations.append("Duplicate story_id found.")

    scenario_ids = [sc.scenario_id for sc in req.scenarios]
    if len(scenario_ids) != len(set(scenario_ids)):
        violations.append("Duplicate scenario_id found.")

    story_id_set = set(story_ids)
    for sc in req.scenarios:
        if sc.story_id not in story_id_set:
            violations.append(
                f"Scenario {sc.scenario_id} references missing story_id {sc.story_id}."
            )

    for s in req.stories:
        if s.epic_id != req.epic_id:
            violations.append(f"Story {s.story_id} epic_id does not match requirement set epic_id.")

    scenario_id_set = set(scenario_ids)
    for s in req.stories:
        mapped = req.trace_map.get(s.story_id)
        if not mapped:
            violations.append(f"trace_map missing scenarios for story {s.story_id}.")
        else:
            for sid in mapped:
                if sid not in scenario_id_set:
                    violations.append(
                        f"trace_map references missing scenario_id {sid} for story {s.story_id}."
                    )

    return (len(violations) == 0), violations
