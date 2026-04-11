from __future__ import annotations

import pytest

from sql_query_reviewer.models import GroundTruthIssue, SQLReviewAction
from server.reward import compute_reward


def _action(action_type: str, confidence: float = 0.5) -> SQLReviewAction:
    if action_type == "identify_issue":
        return SQLReviewAction(
            action_type="identify_issue",
            issue_category="syntax",
            issue_description="some issue",
            confidence=confidence,
        )
    if action_type == "suggest_fix":
        return SQLReviewAction(
            action_type="suggest_fix",
            suggested_fix="SELECT 1;",
            confidence=confidence,
        )
    return SQLReviewAction(action_type=action_type, confidence=confidence)


def _issue(severity: float = 0.35) -> GroundTruthIssue:
    return GroundTruthIssue(
        id="test_issue_001",
        category="syntax",
        description="A test issue.",
        severity=severity,
        fix="SELECT 1;",
        keywords=["test"],
    )


# ── identify_issue ────────────────────────────────────────────────────────────

def test_identify_issue_duplicate_returns_small_penalty() -> None:
    assert compute_reward(_action("identify_issue"), _issue(), duplicate_issue=True) == pytest.approx(-0.02)


def test_identify_issue_no_match_returns_penalty() -> None:
    assert compute_reward(_action("identify_issue"), None) == pytest.approx(-0.1)


def test_identify_issue_match_no_fix_zero_confidence() -> None:
    # base_reward = min(0.35, 0.35) = 0.35; fix_bonus = 0; confidence_bonus = 0
    # order_bonus = 0.04 * (1/(0+1)) = 0.04 → total = 0.39
    assert compute_reward(_action("identify_issue", confidence=0.0), _issue(0.35)) == pytest.approx(0.39)


def test_identify_issue_match_no_fix_full_confidence() -> None:
    # base=0.35 + confidence_bonus=min(0.05, 1.0*0.35*0.08)=0.028 + order_bonus=0.04 → 0.418
    assert compute_reward(_action("identify_issue", confidence=1.0), _issue(0.35)) == pytest.approx(0.418)


def test_identify_issue_match_with_fix_zero_confidence() -> None:
    # base=0.35 + fix_bonus=0.08 + order_bonus=0.04 = 0.47, capped at 0.45
    assert compute_reward(_action("identify_issue", confidence=0.0), _issue(0.35), fix_valid=True) == pytest.approx(0.45)


def test_identify_issue_high_severity_capped_at_035_base() -> None:
    # min(0.9, 0.35) = 0.35 + order_bonus=0.04 = 0.39
    assert compute_reward(_action("identify_issue", confidence=0.0), _issue(severity=0.9)) == pytest.approx(0.39)


# ── suggest_fix ───────────────────────────────────────────────────────────────

def test_suggest_fix_without_previous_issue_is_penalized() -> None:
    assert compute_reward(_action("suggest_fix"), None, has_previous_issue=False) == pytest.approx(-0.05)


def test_suggest_fix_with_previous_issue_invalid_fix() -> None:
    assert compute_reward(_action("suggest_fix"), _issue(), has_previous_issue=True, fix_valid=False) == pytest.approx(0.0)


def test_suggest_fix_with_previous_issue_valid_fix() -> None:
    assert compute_reward(_action("suggest_fix"), _issue(), has_previous_issue=True, fix_valid=True) == pytest.approx(0.1)


# ── approve ───────────────────────────────────────────────────────────────────

def test_approve_all_issues_found_gives_positive_reward() -> None:
    assert compute_reward(_action("approve"), None, remaining_unfound=0) == pytest.approx(0.2)


def test_approve_one_issue_missed_gives_penalty() -> None:
    assert compute_reward(_action("approve"), None, remaining_unfound=1) == pytest.approx(-0.15)


def test_approve_many_issues_missed_floors_at_negative_one() -> None:
    # -0.15 * 7 = -1.05 → floored at -1.0
    assert compute_reward(_action("approve"), None, remaining_unfound=7) == pytest.approx(-1.0)


# ── request_more_context ──────────────────────────────────────────────────────

def test_request_more_context_returns_zero() -> None:
    # No schema_available → returns 0.0
    assert compute_reward(_action("request_more_context"), None) == pytest.approx(0.0)


def test_request_more_context_with_schema_returns_penalty() -> None:
    # schema_available=True → returns -0.03
    assert compute_reward(_action("request_more_context"), None, schema_available=True) == pytest.approx(-0.03)
