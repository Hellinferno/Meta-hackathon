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
    issues_found_count: int = 0,
    schema_available: bool = False,
) -> float:
    if action.action_type == "identify_issue":
        if duplicate_issue:
            return -0.02

        if matched_issue is None:
            return -0.1

        # Base reward scaled by severity
        base_reward = min(matched_issue.severity, 0.35)

        # Fix bonus
        fix_bonus = 0.08 if fix_valid else 0.0

        # Confidence bonus — higher reward for confident correct identifications
        confidence_bonus = min(0.05, action.confidence * matched_issue.severity * 0.08)

        # Discovery order bonus — finding the first issue is worth slightly more
        # This encourages the agent to start identifying issues quickly
        order_bonus = 0.04 * (1.0 / (issues_found_count + 1))

        return min(base_reward + fix_bonus + confidence_bonus + order_bonus, 0.45)

    if action.action_type == "suggest_fix":
        if not has_previous_issue:
            return -0.05
        return 0.1 if fix_valid else 0.0

    if action.action_type == "approve":
        if remaining_unfound == 0:
            return 0.2
        return max(-1.0, -0.15 * remaining_unfound)

    if action.action_type == "request_more_context":
        # Mild penalty for asking when schema is already provided
        if schema_available:
            return -0.03
        return 0.0

    return 0.0
