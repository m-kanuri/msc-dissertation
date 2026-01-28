from __future__ import annotations

from dissertation.models.schemas import GherkinScenario


def validate_scenario(sc: GherkinScenario) -> tuple[bool, list[str]]:
    v: list[str] = []
    if len(sc.given) < 1:
        v.append(f"{sc.scenario_id}: missing GIVEN step(s).")
    if len(sc.when) < 1:
        v.append(f"{sc.scenario_id}: missing WHEN step(s).")
    if len(sc.then) < 1:
        v.append(f"{sc.scenario_id}: missing THEN step(s).")

    weak_then_words = [
        "work",
        "handle",
        "support",
        "appropriate",
        "user-friendly",
        "fast",
        "easily",
    ]
    for t in sc.then:
        lower = t.lower()
        if any(w in lower for w in weak_then_words):
            v.append(f"{sc.scenario_id}: THEN may be non-testable/vague: '{t}'.")

    return (len(v) == 0), v


def validate_all(scenarios: list[GherkinScenario]) -> tuple[bool, list[str]]:
    all_v: list[str] = []
    ok = True
    for sc in scenarios:
        sc_ok, v = validate_scenario(sc)
        ok = ok and sc_ok
        all_v.extend(v)
    return ok, all_v
