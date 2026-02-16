from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from dissertation.core.openai_client import get_client, get_model
from dissertation.models.schemas import Epic, GherkinScenario, UserStory


class GeneratedBundle(BaseModel):
    """
    Validate the model output locally (Pydantic).
    We ask the model for JSON-only output, then validate/repair as needed.
    """

    model_config = ConfigDict(extra="forbid")
    stories: list[UserStory] = Field(min_length=1)
    scenarios: list[GherkinScenario] = Field(min_length=1)
    trace_map: dict[str, list[str]]


SYSTEM_PROMPT = """You are a Requirements Engineering assistant.
Transform the Epic into high-quality User Stories and Gherkin Acceptance Criteria.

Hard rules:
- Output JSON ONLY (no markdown, no commentary).
- Must match this schema exactly (keys and structure): stories[], scenarios[], trace_map.
- IDs: US-001, US-002... and SC-001, SC-002...
- Each story must include epic_id exactly matching the input epic_id.
- Every scenario must have >=1 Given, >=1 When, >=1 Then.
- If unclear, put details in assumptions/open_questions rather than guessing.
"""

USER_PROMPT_TEMPLATE = """Epic ID: {epic_id}

Epic text:
{epic_text}

Constraints:
{constraints}

Glossary:
{glossary}

Return JSON with:
- stories: list of UserStory
- scenarios: list of GherkinScenario
- trace_map: map story_id -> list of scenario_id
"""

ADAPT_PROMPT_TEMPLATE = """You will adapt a prior requirement bundle to a new epic.

NEW EPIC
Epic ID: {epic_id}

Epic text:
{epic_text}

Constraints:
{constraints}

Glossary:
{glossary}

PRIOR REQUIREMENT BUNDLE (from a similar epic; similarity={similarity})
{prior_bundle_json}

TASK
- Adapt the prior bundle so it fits the NEW EPIC and constraints.
- Keep existing story_id and scenario_id values where they still apply.
- Remove items that no longer fit. Add new stories/scenarios if needed.
- Ensure:
  * each story has epic_id = {epic_id}
  * every scenario has >=1 Given, >=1 When, >=1 Then
  * trace_map maps each story_id to its scenario_ids
- Output JSON ONLY matching schema: stories[], scenarios[], trace_map.
"""


def _call_json_mode(prompt_messages: list[dict[str, Any]], model: str) -> str:
    """
    Uses Responses API JSON mode. We pass chat-style {role, content} messages.
    Some IDEs complain about OpenAI SDK type stubs here; runtime supports it.
    """
    client = get_client()

    resp = client.responses.create(
        model=model,
        input=prompt_messages,  # type: ignore[arg-type]
        text={"format": {"type": "json_object"}},  # type: ignore[arg-type]
    )
    return resp.output_text


def _repair_json(raw: str, error: str, model: str) -> str:
    schema_hint = GeneratedBundle.model_json_schema()

    repair_messages: list[dict[str, Any]] = [
        {"role": "system", "content": "You are a JSON repair tool. Output JSON only."},
        {
            "role": "user",
            "content": (
                "Fix the following JSON so it matches the required schema.\n\n"
                f"Schema (JSON Schema):\n{json.dumps(schema_hint, indent=2)}\n\n"
                f"Validation error:\n{error}\n\n"
                f"Bad JSON:\n{raw}\n\n"
                "Return ONLY the corrected JSON."
            ),
        },
    ]

    return _call_json_mode(repair_messages, model=model)


def generate_with_openai(
    epic: Epic,
    *,
    draft_bundle: dict[str, Any] | None = None,
    mode: str = "fresh",
    similarity: float | None = None,
    max_retries: int = 2,
) -> GeneratedBundle:
    model = get_model()

    glossary_text = "\n".join([f"- {g.term}: {g.definition}" for g in epic.glossary]) or "(none)"
    constraints_text = "\n".join([f"- {c}" for c in epic.constraints]) or "(none)"

    if draft_bundle is None:
        # fresh generation (current behaviour)
        user_prompt = USER_PROMPT_TEMPLATE.format(
            epic_id=epic.epic_id,
            epic_text=epic.text.strip(),
            constraints=constraints_text,
            glossary=glossary_text,
        )
        system_prompt = SYSTEM_PROMPT
    else:
        # semantic adaptation
        prior_bundle_json = json.dumps(draft_bundle, indent=2)
        sim_value = similarity if similarity is not None else 0.0

        user_prompt = ADAPT_PROMPT_TEMPLATE.format(
            epic_id=epic.epic_id,
            epic_text=epic.text.strip(),
            constraints=constraints_text,
            glossary=glossary_text,
            similarity=f"{sim_value:.2f}",
            prior_bundle_json=prior_bundle_json,
        )

        system_prompt = (
            SYSTEM_PROMPT
            + "\nAdditional rule: You are adapting an existing bundle; preserve IDs where possible."
        )

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    raw = _call_json_mode(messages, model=model)

    for attempt in range(max_retries + 1):
        try:
            data = json.loads(raw)
            return GeneratedBundle.model_validate(data)

        except (json.JSONDecodeError, ValidationError) as e:
            if attempt >= max_retries:
                raise
            raw = _repair_json(raw=raw, error=str(e), model=model)

    raise RuntimeError("Unreachable")
