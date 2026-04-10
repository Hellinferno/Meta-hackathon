from __future__ import annotations

import re

from sql_query_reviewer.models import GroundTruthIssue, IssueCategory, SQLReviewAction

TOKEN_RE = re.compile(r"[a-zA-Z0-9_]+")


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def normalize_text(value: str) -> str:
    return " ".join(TOKEN_RE.findall(value.lower()))


def tokenize(value: str) -> set[str]:
    return set(TOKEN_RE.findall(value.lower()))


def _set_overlap(candidate: set[str], target: set[str]) -> float:
    if not candidate or not target:
        return 0.0
    return len(candidate & target) / max(len(target), 1)


def score_issue_match(description: str, category: IssueCategory | None, issue: GroundTruthIssue) -> float:
    candidate_tokens = tokenize(description)
    keyword_tokens = set(issue.keywords)
    description_tokens = tokenize(issue.description)
    keyword_score = _set_overlap(candidate_tokens, keyword_tokens)
    description_score = _set_overlap(candidate_tokens, description_tokens)
    category_bonus = 0.2 if category == issue.category else 0.0
    score = (keyword_score * 0.6) + (description_score * 0.25) + category_bonus
    return clamp(score, 0.0, 1.0)


def match_issue(
    action: SQLReviewAction,
    ground_truth_issues: list[GroundTruthIssue],
    already_found_ids: set[str],
) -> tuple[GroundTruthIssue | None, float]:
    if not action.issue_description:
        return None, 0.0

    best_issue: GroundTruthIssue | None = None
    best_score = 0.0
    for issue in ground_truth_issues:
        if issue.id in already_found_ids:
            continue
        score = score_issue_match(action.issue_description, action.issue_category, issue)
        if score > best_score:
            best_score = score
            best_issue = issue

    if best_issue is None or best_score < 0.35:
        return None, best_score
    return best_issue, best_score


def validate_fix(suggested_fix: str | None, issue: GroundTruthIssue) -> bool:
    if not suggested_fix:
        return False
    suggestion_tokens = tokenize(suggested_fix)
    canonical_tokens = tokenize(issue.fix)
    if not suggestion_tokens or not canonical_tokens:
        return False
    overlap = _set_overlap(suggestion_tokens, canonical_tokens)
    description_overlap = _set_overlap(suggestion_tokens, tokenize(issue.description))
    return overlap >= 0.5 or description_overlap >= 0.6


def grade_episode(
    found_issue_ids: set[str],
    ground_truth_issues: list[GroundTruthIssue],
    total_steps: int,
    max_steps: int,
    false_positive_count: int,
) -> float:
    if not ground_truth_issues:
        return 0.99 if false_positive_count == 0 else clamp(1.0 - (0.1 * false_positive_count), 0.01, 0.99)

    total_severity = sum(issue.severity for issue in ground_truth_issues)
    found_severity = sum(issue.severity for issue in ground_truth_issues if issue.id in found_issue_ids)
    coverage_score = found_severity / total_severity if total_severity else 0.0
    efficiency_bonus = max(0.0, 0.1 * (1 - (total_steps / max(max_steps, 1))))
    false_positive_penalty = 0.05 * false_positive_count
    final_score = coverage_score + efficiency_bonus - false_positive_penalty
    return clamp(final_score, 0.01, 0.99)

