"""
Inference Script — SQL Query Reviewer
======================================
MANDATORY environment variables:
    API_BASE_URL   The API endpoint for the LLM.
    MODEL_NAME     The model identifier to use for inference.
    HF_TOKEN       Your Hugging Face / API key.

STDOUT FORMAT:
    [START] task=<task_name> env=<benchmark> model=<model_name>
    [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>
"""

from __future__ import annotations

import json
import os
from typing import Any, List, Optional

from openai import OpenAI

from sql_query_reviewer.client import SyncSQLReviewEnv
from sql_query_reviewer.models import SQLReviewAction, SQLReviewObservation

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_TASK_IDS = ("easy_001", "medium_001", "hard_001")
BENCHMARK = "sql-query-reviewer"
SUCCESS_SCORE_THRESHOLD = 0.1

ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:8000")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
API_KEY = os.getenv("HF_TOKEN") or os.getenv("OPENAI_API_KEY") or os.getenv("API_KEY")

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

# ---------------------------------------------------------------------------
# Structured stdout logging — MUST match the hackathon spec exactly
# ---------------------------------------------------------------------------


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(
    step: int, action: str, reward: float, done: bool, error: Optional[str]
) -> None:
    done_str = str(done).lower()
    error_str = error if error else "null"
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} "
        f"done={done_str} error={error_str}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} "
        f"score={score:.2f} rewards={rewards_str}",
        flush=True,
    )


# ---------------------------------------------------------------------------
# LLM interaction
# ---------------------------------------------------------------------------


def build_user_prompt(observation: SQLReviewObservation) -> str:
    payload = {
        "query": observation.query,
        "schema_info": observation.schema_info,
        "context": observation.context,
        "issues_found_so_far": [
            issue.model_dump() for issue in observation.issues_found_so_far
        ],
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


def choose_action(
    llm_client: OpenAI, model_name: str, observation: SQLReviewObservation
) -> SQLReviewAction:
    try:
        response = llm_client.chat.completions.create(
            model=model_name,
            temperature=0,
            max_tokens=300,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(observation)},
            ],
        )
        content = response.choices[0].message.content or ""
        return SQLReviewAction.model_validate(extract_json(content))
    except Exception as exc:
        print(f"[DEBUG] Model request failed: {exc}", flush=True)
        # Fallback: approve to end the episode gracefully
        return SQLReviewAction(action_type="approve", confidence=0.1)


# ---------------------------------------------------------------------------
# Episode runner
# ---------------------------------------------------------------------------


def run_episode(
    env: SyncSQLReviewEnv, llm_client: OpenAI, model_name: str, task_id: str
) -> None:
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False
    last_error: Optional[str] = None

    log_start(task=task_id, env=BENCHMARK, model=model_name)

    try:
        result = env.reset(task_id=task_id)

        step = 0
        while not result.done:
            step += 1
            action = choose_action(
                llm_client=llm_client,
                model_name=model_name,
                observation=result.observation,
            )

            action_str = action.action_type
            if action.issue_description:
                # Keep action string short and readable
                action_str = f"{action.action_type}({action.issue_category})"

            result = env.step(action)

            reward = result.reward
            rewards.append(reward)
            steps_taken = step
            last_error = result.info.get("error") if result.info else None

            log_step(
                step=step,
                action=action_str,
                reward=reward,
                done=result.done,
                error=last_error,
            )

        # Get final score from state
        state = env.state()
        score = state.final_score if state.final_score is not None else 0.0
        success = score >= SUCCESS_SCORE_THRESHOLD

    except Exception as exc:
        print(f"[DEBUG] Episode error: {exc}", flush=True)
        last_error = str(exc)

    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    if not API_KEY:
        raise SystemExit("Set HF_TOKEN or OPENAI_API_KEY before running inference.py")

    task_ids = tuple(
        tid.strip()
        for tid in os.getenv("TASK_IDS", ",".join(DEFAULT_TASK_IDS)).split(",")
        if tid.strip()
    )

    llm_client = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)

    with SyncSQLReviewEnv(base_url=ENV_BASE_URL) as env:
        for task_id in task_ids:
            run_episode(
                env=env,
                llm_client=llm_client,
                model_name=MODEL_NAME,
                task_id=task_id,
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
