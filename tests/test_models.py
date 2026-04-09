import pytest
from pydantic import ValidationError

from sql_query_reviewer.models import SQLReviewAction


def test_identify_issue_requires_category_and_description() -> None:
    with pytest.raises(ValidationError):
        SQLReviewAction(action_type="identify_issue", confidence=0.8)


def test_suggest_fix_requires_fix_text() -> None:
    with pytest.raises(ValidationError):
        SQLReviewAction(action_type="suggest_fix")


def test_approve_action_is_valid_without_optional_fields() -> None:
    action = SQLReviewAction(action_type="approve", confidence=0.9)
    assert action.action_type == "approve"
    assert action.issue_description is None

