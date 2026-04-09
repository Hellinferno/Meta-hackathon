from sql_query_reviewer.models import SQLReviewAction, TaskRecord
from server.grader import grade_episode, match_issue, validate_fix
from server.environment import SQLReviewEnvironment


def test_match_issue_finds_expected_easy_issue() -> None:
    environment = SQLReviewEnvironment()
    task = environment.tasks["easy_002"]
    action = SQLReviewAction(
        action_type="identify_issue",
        issue_category="syntax",
        issue_description="The query is missing the FROM clause before users.",
        confidence=0.95,
    )

    match, score = match_issue(action, task.ground_truth_issues, set())

    assert match is not None
    assert match.id == "easy_002_missing_from"
    assert score >= 0.35


def test_validate_fix_accepts_expected_remediation() -> None:
    environment = SQLReviewEnvironment()
    task = environment.tasks["easy_003"]
    assert validate_fix("SELECT order_id, total FROM orders WHERE shipped_at IS NULL;", task.ground_truth_issues[0])


def test_grade_episode_is_deterministic_and_bounded() -> None:
    environment = SQLReviewEnvironment()
    task = environment.tasks["medium_001"]

    first = grade_episode({"medium_001_select_star"}, task.ground_truth_issues, total_steps=2, max_steps=5, false_positive_count=1)
    second = grade_episode({"medium_001_select_star"}, task.ground_truth_issues, total_steps=2, max_steps=5, false_positive_count=1)

    assert first == second
    assert 0.0 <= first <= 1.0

