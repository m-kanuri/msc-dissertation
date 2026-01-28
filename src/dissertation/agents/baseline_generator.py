from __future__ import annotations

from dissertation.models.schemas import Epic, GherkinScenario, UserStory


def generate_baseline(epic: Epic):
    """
    Generate a minimal baseline UserStory + GherkinScenario when an Epic is underspecified.

    Why this exists:
    - Ensures downstream pipelines always have at least one story + scenario to work with.
    - Provides a consistent fallback structure for demos, validation, or early-stage epics.

    Notes:
    - IDs are currently hard-coded to a single baseline (US-001 / SC-001). If multiple
      baselines can be generated per epic, replace with an ID factory/sequence.
    - Text is intentionally generic; it should be replaced/expanded when epic details
      are available.
    """
    story = UserStory(
        story_id="US-001",
        epic_id=epic.epic_id,
        role="user",
        goal="achieve the capability described in the epic",
        benefit="fulfil the epic requirement",
        story_text="As a user, I want the system to fulfil the epic requirement so that I can achieve the intended outcome.",
        assumptions=["Epic lacks detail; clarification may be required."],
        open_questions=["What are the exact success criteria and constraints?"],
    )

    scenario = GherkinScenario(
        scenario_id="SC-001",
        story_id="US-001",
        title="Basic success path",
        given=["Given the user has access to the system"],
        when=["When the user performs the primary action described by the epic"],
        then=["Then the system produces the expected outcome described by the epic"],
    )

    return [story], [scenario], {"US-001": ["SC-001"]}
