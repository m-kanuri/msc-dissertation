from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Mode = Literal["human", "llm_baseline", "agentic"]


class GlossaryTerm(BaseModel):
    model_config = ConfigDict(extra="forbid")
    term: str
    definition: str


class Epic(BaseModel):
    model_config = ConfigDict(extra="forbid")
    epic_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    glossary: list[GlossaryTerm] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)


class UserStory(BaseModel):
    model_config = ConfigDict(extra="forbid")
    story_id: str = Field(min_length=1)
    epic_id: str = Field(min_length=1)
    role: str = Field(min_length=1)
    goal: str = Field(min_length=1)
    benefit: str = Field(min_length=1)
    story_text: str = Field(min_length=1)
    assumptions: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)


class GherkinScenario(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scenario_id: str = Field(min_length=1)
    story_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    given: list[str] = Field(default_factory=list)
    when: list[str] = Field(default_factory=list)
    then: list[str] = Field(default_factory=list)


class InvestScores(BaseModel):
    model_config = ConfigDict(extra="forbid")
    I: int = Field(ge=1, le=5)  # noqa: E741
    N: int = Field(ge=1, le=5)
    V: int = Field(ge=1, le=5)
    E: int = Field(ge=1, le=5)
    S: int = Field(ge=1, le=5)
    T: int = Field(ge=1, le=5)


class QualityReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    story_id: str
    invest: InvestScores
    gherkin_valid: bool
    ambiguities: list[str] = Field(default_factory=list)
    violations: list[str] = Field(default_factory=list)
    overall_score: float = Field(ge=1.0, le=5.0)


class RunMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")
    run_id: str
    epic_id: str
    mode: Mode
    iteration: int
    model_name: str | None = None
    temperature: float | None = None


class RequirementSet(BaseModel):
    model_config = ConfigDict(extra="forbid")
    epic_id: str
    mode: Mode
    stories: list[UserStory]
    scenarios: list[GherkinScenario]
    quality_reports: list[QualityReport]
    trace_map: dict[str, list[str]]  # story_id -> [scenario_id...]
    run_metadata: RunMetadata
