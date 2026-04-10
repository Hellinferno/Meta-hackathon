from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Difficulty = Literal["easy", "medium", "hard"]
ActionType = Literal["identify_issue", "suggest_fix", "approve", "request_more_context"]
IssueCategory = Literal["syntax", "performance", "security", "logic", "style"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class GroundTruthIssue(StrictModel):
    id: str = Field(min_length=1)
    category: IssueCategory
    description: str = Field(min_length=1)
    severity: float = Field(gt=0.0, le=1.0)
    fix: str = Field(min_length=1)
    keywords: list[str] = Field(default_factory=list)

    @field_validator("keywords")
    @classmethod
    def normalize_keywords(cls, value: list[str]) -> list[str]:
        deduped: list[str] = []
        for keyword in value:
            normalized = keyword.strip().lower()
            if normalized and normalized not in deduped:
                deduped.append(normalized)
        return deduped


class TaskRecord(StrictModel):
    task_id: str = Field(min_length=1)
    difficulty: Difficulty
    query: str = Field(min_length=1)
    schema_info: dict[str, dict[str, str]] = Field(default_factory=dict, alias="schema")
    context: str = Field(min_length=1)
    ground_truth_issues: list[GroundTruthIssue] = Field(default_factory=list)
    max_steps: int = Field(ge=1, le=12)


class IdentifiedIssue(StrictModel):
    issue_id: str = Field(min_length=1)
    category: IssueCategory
    description: str = Field(min_length=1)


class SQLReviewAction(StrictModel):
    action_type: ActionType
    issue_category: IssueCategory | None = None
    issue_description: str | None = None
    suggested_fix: str | None = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_action(self) -> "SQLReviewAction":
        if self.action_type == "identify_issue":
            if not self.issue_category or not self.issue_description:
                raise ValueError("identify_issue requires issue_category and issue_description")
        elif self.action_type == "suggest_fix":
            if not self.suggested_fix:
                raise ValueError("suggest_fix requires suggested_fix")
        return self


class SQLReviewObservation(StrictModel):
    query: str
    schema_info: dict[str, dict[str, str]] = Field(default_factory=dict)
    context: str
    issues_found_so_far: list[IdentifiedIssue] = Field(default_factory=list)
    remaining_actions: int = Field(ge=0)
    difficulty: Difficulty
    feedback: str


class SQLReviewState(StrictModel):
    task_id: str
    step_count: int = Field(default=0, ge=0)
    issues_identified: list[IdentifiedIssue] = Field(default_factory=list)
    total_reward: float = 0.0
    done: bool = False
    approved: bool = False
    fixes_suggested: list[str] = Field(default_factory=list)
    false_positive_count: int = Field(default=0, ge=0)
    final_score: float | None = Field(default=None, gt=0.0, lt=1.0)


class StepResult(StrictModel):
    observation: SQLReviewObservation
    reward: float
    done: bool
    info: dict[str, Any] = Field(default_factory=dict)


class ResetRequest(StrictModel):
    task_id: str | None = None
