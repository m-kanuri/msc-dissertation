from __future__ import annotations

import json

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from dissertation.core.openai_client import get_client, get_model
from dissertation.models.schemas import Epic, GherkinScenario, UserStory


class GeneratedBundle(BaseModel):
    """
    Local schema validation (Pydantic). We use OpenAI JSON mode to ensure valid JSON,
    then validate/repair locally for "no room for error" robustness.
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


def _call_json_mode(prompt_messages: list[dict], model: str) -> str:
    """
    Uses JSON mode. In Responses API this is done via:
    text: { format: { type: "json_object" } }
    which asks the model to output valid JSON. :contentReference[oaicite:1]{index=1}
    """
    client = get_client()
    resp = client.responses.create(
        model=model,
        input=prompt_messages,
        text={"format": {"type": "json_object"}},
    )
    return resp.output_text


def _repair_json(raw: str, error: str, model: str) -> str:
    schema_hint = GeneratedBundle.model_json_schema()
    repair_messages = [
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


def generate_with_openai(epic: Epic, *, max_retries: int = 2) -> GeneratedBundle:
    model = get_model()

    glossary_text = "\n".join([f"- {g.term}: {g.definition}" for g in epic.glossary]) or "(none)"
    constraints_text = "\n".join([f"- {c}" for c in epic.constraints]) or "(none)"

    user_prompt = USER_PROMPT_TEMPLATE.format(
        epic_id=epic.epic_id,
        epic_text=epic.text.strip(),
        constraints=constraints_text,
        glossary=glossary_text,
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    raw = _call_json_mode(messages, model=model)

    for attempt in range(max_retries + 1):
        try:
            data = json.loads(raw)
            bundle = GeneratedBundle.model_validate(data)
            return bundle
        except (json.JSONDecodeError, ValidationError) as e:
            if attempt >= max_retries:
                raise
            raw = _repair_json(raw=raw, error=str(e), model=model)

    raise RuntimeError("Unreachable")
