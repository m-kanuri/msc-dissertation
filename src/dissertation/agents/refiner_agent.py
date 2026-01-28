from __future__ import annotations

import json

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from dissertation.agents.critic_agent import Critique
from dissertation.core.openai_client import get_client, get_model
from dissertation.models.schemas import Epic, GherkinScenario, RequirementSet, UserStory


class RefinedBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")
    stories: list[UserStory] = Field(min_length=1)
    scenarios: list[GherkinScenario] = Field(min_length=1)
    trace_map: dict[str, list[str]]


SYSTEM_PROMPT = """You are a Requirements Engineering Refiner.
Apply the Critique edit instructions to improve the RequirementSet.

Rules:
- Output JSON only.
- Must match schema: stories[], scenarios[], trace_map.
- Preserve existing IDs where possible.
- If splitting, continue numbering (US-002 etc / SC-002 etc).
- Every scenario must include >=1 Given, >=1 When, >=1 Then.
- Do not expand scope beyond the Epic; add open_questions instead of guessing.
"""


def _call_json_mode(messages: list[dict], model: str) -> str:
    client = get_client()
    resp = client.responses.create(
        model=model,
        input=messages,
        text={"format": {"type": "json_object"}},
    )
    return resp.output_text


def _repair_json(raw: str, error: str, model: str) -> str:
    schema_hint = RefinedBundle.model_json_schema()
    messages = [
        {"role": "system", "content": "You are a JSON repair tool. Output JSON only."},
        {
            "role": "user",
            "content": (
                "Fix the JSON to match the required schema.\n\n"
                f"Schema:\n{json.dumps(schema_hint, indent=2)}\n\n"
                f"Validation error:\n{error}\n\n"
                f"Bad JSON:\n{raw}\n\n"
                "Return ONLY corrected JSON."
            ),
        },
    ]
    return _call_json_mode(messages, model=model)


def refine(
    epic: Epic, req: RequirementSet, critique: Critique, *, max_retries: int = 2
) -> RefinedBundle:
    model = get_model()

    payload = {
        "epic": epic.model_dump(),
        "requirement_set": req.model_dump(),
        "critique": critique.model_dump(),
    }

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Apply edits to this JSON:\n{json.dumps(payload, indent=2)}"},
    ]

    raw = _call_json_mode(messages, model=model)

    for attempt in range(max_retries + 1):
        try:
            data = json.loads(raw)
            return RefinedBundle.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as e:
            if attempt >= max_retries:
                raise
            raw = _repair_json(raw, str(e), model=model)

    raise RuntimeError("Unreachable")
