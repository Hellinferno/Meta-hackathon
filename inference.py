from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

from sql_query_reviewer.client import SyncSQLReviewEnv
from sql_query_reviewer.models import SQLReviewAction, SQLReviewObservation

DEFAULT_TASK_IDS = ("easy_001", "medium_001", "hard_001")

SYSTEM_PROMPT = """You are reviewing a SQL query for correctness, performance, and security.
Return exactly one JSON object with these keys:
- action_type: identify_issue, suggest_fix, approve, or request_more_context
- issue_category: syntax, performance, security, logic, or style when relevant
- issue_description: concise issue statement when relevant
- suggested_fix: corrected SQL or corrected fragment when relevant
- confidence: float between 0.0 and 1.0

Guidelines:
- Prefer identify_issue until you have high confidence all important issues are covered.
- Use approve only when the query looks acceptable or all issues have already been identified.
- Keep the JSON valid and do not wrap it in prose.
"""


def print_event(prefix: str, payload: dict[str, Any]) -> None:
    print(f"[{prefix}] {json.dumps(payload, sort_keys=True)}")


def build_user_prompt(observation: SQLReviewObservation) -> str:
    payload = {
        "query": observation.query,
        "schema_info": observation.schema_info,
        "context": observation.context,
        "issues_found_so_far": [issue.model_dump() for issue in observation.issues_found_so_far],
        "remaining_actions": observation.remaining_actions,
        "difficulty": observation.difficulty,
        "feedback": observation.feedback,
    }
    return json.dumps(payload, indent=2)


def extract_json(content: str) -> dict[str, Any]:
    stripped = content.strip()
    if stripped.startswith("```"):
        lines = [line for line in stripped.splitlines() if not line.startswith("```")]
        stripped = "\n".join(lines).strip()

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"Could not find JSON object in model response: {content!r}")
    return json.loads(stripped[start : end + 1])


def choose_action(llm_client: Any, model_name: str, observation: SQLReviewObservation) -> SQLReviewAction:
    response = llm_client.chat.completions.create(
        model=model_name,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(observation)},
        ],
    )
    content = response.choices[0].message.content or ""
    return SQLReviewAction.model_validate(extract_json(content))


def run_episode(env: Any, llm_client: Any, model_name: str, task_id: str) -> dict[str, Any]:
    result = env.reset(task_id=task_id)
    print_event(
        "START",
        {
            "difficulty": result.observation.difficulty,
            "remaining_actions": result.observation.remaining_actions,
            "task_id": task_id,
        },
    )

    while True:
        action = choose_action(llm_client=llm_client, model_name=model_name, observation=result.observation)
        result = env.step(action)
        print_event(
            "STEP",
            {
                "action": action.model_dump(exclude_none=True),
                "done": result.done,
                "feedback": result.observation.feedback,
                "reward": result.reward,
                "task_id": task_id,
            },
        )
        if result.done:
            state = env.state()
            summary = {
                "final_score": state.final_score,
                "steps": state.step_count,
                "task_id": task_id,
                "total_reward": state.total_reward,
            }
            print_event("END", summary)
            return summary


def main() -> int:
    env_base_url = os.getenv("ENV_BASE_URL", "http://localhost:8000")
    api_base_url = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
    model_name = os.getenv("MODEL_NAME", "gpt-4o-mini")
    api_key = os.getenv("HF_TOKEN") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("Set HF_TOKEN or OPENAI_API_KEY before running inference.py")

    task_ids = tuple(
        task_id.strip()
        for task_id in os.getenv("TASK_IDS", ",".join(DEFAULT_TASK_IDS)).split(",")
        if task_id.strip()
    )

    llm_client = OpenAI(api_key=api_key, base_url=api_base_url)
    with SyncSQLReviewEnv(base_url=env_base_url) as env:
        for task_id in task_ids:
            run_episode(env=env, llm_client=llm_client, model_name=model_name, task_id=task_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

