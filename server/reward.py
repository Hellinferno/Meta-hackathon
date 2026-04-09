from __future__ import annotations

from sql_query_reviewer.models import GroundTruthIssue, SQLReviewAction


def compute_reward(
    action: SQLReviewAction,
    matched_issue: GroundTruthIssue | None,
    *,
    fix_valid: bool = False,
    duplicate_issue: bool = False,
    remaining_unfound: int = 0,
    has_previous_issue: bool = False,
) -> float:
    if action.action_type == "identify_issue":
        if duplicate_issue:
            return -0.02
        if matched_issue is None:
            return -0.1
        base_reward = min(matched_issue.severity, 0.35)
        fix_bonus = 0.08 if fix_valid else 0.0
        confidence_bonus = min(0.05, action.confidence * 0.05)
        return min(base_reward + fix_bonus + confidence_bonus, 0.4)

    if action.action_type == "suggest_fix":
        if not has_previous_issue:
            return -0.05
        return 0.1 if fix_valid else 0.0

    if action.action_type == "approve":
        if remaining_unfound == 0:
            return 0.2
        return max(-1.0, -0.15 * remaining_unfound)

    return 0.0

