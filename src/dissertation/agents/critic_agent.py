from __future__ import annotations

import json
from typing import Any, Literal, cast

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from dissertation.core.openai_client import get_client, get_model
from dissertation.models.schemas import Epic, RequirementSet

IssueType = Literal[
    "INVEST_Independent",
    "INVEST_Negotiable",
    "INVEST_Valuable",
    "INVEST_Estimable",
    "INVEST_Small",
    "INVEST_Testable",
    "Gherkin_Structure",
    "Ambiguity",
    "Traceability",
    "Other",
]

ActionType = Literal[
    "rewrite_story",
    "split_story",
    "revise_scenario",
    "add_scenario",
    "clarify_assumptions",
]


class EditInstruction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    issue_type: IssueType
    target_id: str = Field(description="Existing story_id or scenario_id (US-xxx / SC-xxx)")
    action: ActionType
    rationale: str
    patch_guidance: str = Field(description="Concrete instructions the refiner must apply")


class Critique(BaseModel):
    model_config = ConfigDict(extra="forbid")
    should_iterate: bool
    summary: str
    edits: list[EditInstruction] = Field(default_factory=list)


SYSTEM_PROMPT = """You are a Requirements Engineering Critic.
You do NOT rewrite stories. You identify issues and output edit instructions.

Rules:
- Output JSON only (no markdown).
- Must match the schema exactly: should_iterate, summary, edits[].
- Only reference IDs that exist in the current RequirementSet.
- Be strict about INVEST and Given/When/Then completeness.
- patch_guidance must be actionable and specific.
"""


def _call_json_mode(messages: list[dict[str, str]], model: str) -> str:
    client = get_client()
    resp = client.responses.create(
        model=model,
        input=cast(Any, messages),  # OpenAI SDK typing is strict; runtime is fine
        text=cast(Any, {"format": {"type": "json_object"}}),
    )
    return resp.output_text


def _repair_json(raw: str, error: str, model: str) -> str:
    schema_hint = Critique.model_json_schema()
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


def critique(epic: Epic, req: RequirementSet, *, max_retries: int = 2) -> Critique:
    model = get_model()

    payload = {
        "epic": epic.model_dump(),
        "requirement_set": req.model_dump(),
    }

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Critique this JSON:\n{json.dumps(payload, indent=2)}"},
    ]

    raw = _call_json_mode(messages, model=model)

    for attempt in range(max_retries + 1):
        try:
            data = json.loads(raw)
            return Critique.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as e:
            if attempt >= max_retries:
                raise
            raw = _repair_json(raw, str(e), model=model)

    raise RuntimeError("Unreachable")
