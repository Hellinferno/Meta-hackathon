from fastapi.testclient import TestClient

from server.app import create_app
from server.environment import SQLReviewEnvironment


def build_client() -> TestClient:
    return TestClient(create_app(SQLReviewEnvironment()))


def test_reset_returns_initial_observation() -> None:
    client = build_client()

    response = client.post("/reset", json={"task_id": "easy_001"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["observation"]["difficulty"] == "easy"
    assert payload["reward"] == 0.0
    assert payload["done"] is False


def test_identify_issue_returns_positive_reward_for_match() -> None:
    client = build_client()
    client.post("/reset", json={"task_id": "easy_002"})

    response = client.post(
        "/step",
        json={
            "action_type": "identify_issue",
            "issue_category": "syntax",
            "issue_description": "The query is missing the FROM clause before users.",
            "confidence": 0.95,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["reward"] > 0
    assert payload["info"]["issue_id"] == "easy_002_missing_from"


def test_suggest_fix_without_identifying_issue_is_penalized() -> None:
    client = build_client()
    client.post("/reset", json={"task_id": "easy_002"})

    response = client.post(
        "/step",
        json={
            "action_type": "suggest_fix",
            "suggested_fix": "SELECT id, email FROM users WHERE active = 1;",
            "confidence": 0.8,
        },
    )

    assert response.status_code == 200
    assert response.json()["reward"] < 0


def test_approve_with_missed_issues_ends_episode_with_penalty() -> None:
    client = build_client()
    client.post("/reset", json={"task_id": "easy_001"})

    response = client.post("/step", json={"action_type": "approve", "confidence": 0.8})

    assert response.status_code == 200
    payload = response.json()
    assert payload["done"] is True
    assert payload["reward"] < 0
    assert payload["info"]["final_score"] is not None


def test_identify_then_approve_can_finish_successfully() -> None:
    client = build_client()
    client.post("/reset", json={"task_id": "easy_002"})
    client.post(
        "/step",
        json={
            "action_type": "identify_issue",
            "issue_category": "syntax",
            "issue_description": "The query is missing the FROM clause before users.",
            "confidence": 0.95,
        },
    )

    response = client.post("/step", json={"action_type": "approve", "confidence": 0.9})

    assert response.status_code == 200
    payload = response.json()
    assert payload["done"] is True
    assert payload["reward"] > 0
    assert payload["info"]["final_score"] is not None

