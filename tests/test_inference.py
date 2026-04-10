from types import SimpleNamespace

import inference
from sql_query_reviewer.models import SQLReviewObservation, SQLReviewState, StepResult


def test_extract_json_handles_code_fence() -> None:
    payload = inference.extract_json(
        """```json
        {"action_type":"approve","confidence":0.8}
        ```"""
    )
    assert payload["action_type"] == "approve"


def test_run_episode_emits_start_step_end_logs(capsys) -> None:
    class DummyEnv:
        def reset(self, task_id: str) -> StepResult:
            return StepResult(
                observation=SQLReviewObservation(
                    query="SELECT 1;",
                    schema_info={},
                    context="Health check query.",
                    issues_found_so_far=[],
                    remaining_actions=1,
                    difficulty="easy",
                    feedback="Review this query.",
                ),
                reward=0.0,
                done=False,
                info={},
            )

        def step(self, action):
            assert action.action_type == "approve"
            return StepResult(
                observation=SQLReviewObservation(
                    query="SELECT 1;",
                    schema_info={},
                    context="Health check query.",
                    issues_found_so_far=[],
                    remaining_actions=0,
                    difficulty="easy",
                    feedback="Query approved with full issue coverage.",
                ),
                reward=0.2,
                done=True,
                info={},
            )

        def state(self) -> SQLReviewState:
            return SQLReviewState(
                task_id="easy_999",
                step_count=1,
                total_reward=0.2,
                done=True,
                approved=True,
                final_score=0.99,
            )

    class DummyCompletions:
        def create(self, **_kwargs):
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content='{"action_type":"approve","confidence":0.9}')
                    )
                ]
            )

    class DummyClient:
        def __init__(self) -> None:
            self.chat = SimpleNamespace(completions=DummyCompletions())

    inference.run_episode(DummyEnv(), DummyClient(), "dummy-model", "easy_999")
    captured = capsys.readouterr().out

    assert "[START]" in captured
    assert "task=easy_999" in captured
    assert "[STEP]" in captured
    assert "[END]" in captured
    assert "success=true" in captured
    assert "score=0.99" in captured

