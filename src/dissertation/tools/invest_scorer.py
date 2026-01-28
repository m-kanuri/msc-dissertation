from __future__ import annotations

from dissertation.models.schemas import GherkinScenario, InvestScores, UserStory


def score_story_invest(
    story: UserStory, scenarios: list[GherkinScenario]
) -> tuple[InvestScores, list[str]]:
    issues: list[str] = []

    text = story.story_text.lower()
    has_and = " and " in text

    independence = 5
    for w in ["depends on", "after ", "before ", "blocked by", "requires"]:
        if w in text:
            independence = 3
            issues.append(f"{story.story_id}: Independence risk due to '{w}'.")
            break

    N = 5
    for w in ["database", "api", "microservice", "kubernetes", "sql", "react", "ui button"]:
        if w in text:
            N = 3
            issues.append(f"{story.story_id}: Negotiability risk (implementation detail: '{w}').")
            break

    V = 5 if story.benefit.strip() else 2
    if V < 5:
        issues.append(f"{story.story_id}: Missing/weak benefit statement.")

    E = 5
    for w in ["etc", "various", "some", "appropriate", "all possible", "any"]:
        if w in text:
            E = 3
            issues.append(f"{story.story_id}: Estimability risk (vague term: '{w}').")
            break

    S = 4 if has_and else 5
    if has_and:
        issues.append(f"{story.story_id}: Possibly too large (contains 'and').")

    related = [sc for sc in scenarios if sc.story_id == story.story_id]
    T = 2
    if related and all(len(sc.then) >= 1 for sc in related):
        T = 4
    if T < 4:
        issues.append(f"{story.story_id}: Testability weak (missing/weak THEN steps).")

    scores = InvestScores(I=independence, N=N, V=V, E=E, S=S, T=T)
    return scores, issues
