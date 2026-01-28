from __future__ import annotations

from dissertation.models.schemas import Epic, GherkinScenario, UserStory

AMBIGUOUS_TERMS = {
    "fast",
    "quick",
    "easy",
    "easily",
    "simple",
    "user-friendly",
    "appropriate",
    "support",
    "handle",
    "robust",
    "asap",
    "soon",
    "etc",
    "various",
    "some",
    "normally",
    "should",
    "could",
    "may",
}


def detect_ambiguities(
    epic: Epic, stories: list[UserStory], scenarios: list[GherkinScenario]
) -> list[str]:

    hits: list[str] = []

    def scan(text: str, label: str):
        lower = text.lower()
        for term in AMBIGUOUS_TERMS:
            if term in lower:
                hits.append(f"{label}: ambiguous term '{term}' in '{text}'")

        # Placeholder: you can later add an undefined-term check using glossary_terms.

    for s in stories:
        scan(s.story_text, f"{s.story_id}.story_text")
        for a in s.assumptions:
            scan(a, f"{s.story_id}.assumption")
        for q in s.open_questions:
            scan(q, f"{s.story_id}.open_question")

    for sc in scenarios:
        for line in sc.given + sc.when + sc.then:
            scan(line, f"{sc.scenario_id}")

    return hits
