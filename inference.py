"""
Inference Script — SQL Query Reviewer
======================================
MANDATORY environment variables:
    API_BASE_URL       The API endpoint for the LLM.
    MODEL_NAME         The model identifier to use for inference.
    HF_TOKEN           Your Hugging Face / API key.
    LOCAL_IMAGE_NAME   The name of the local Docker image for the environment.

STDOUT FORMAT (must match exactly):
    [START] task=<task_name> env=<benchmark> model=<model_name>
    [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import traceback
from typing import Any, List, Optional

from openai import OpenAI

# ---------------------------------------------------------------------------
# Environment variables — read ALL names the validator might set
# ---------------------------------------------------------------------------

IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME") or os.getenv("IMAGE_NAME")
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:8000")

BENCHMARK = "sql-query-reviewer"
MAX_STEPS = 10
SUCCESS_SCORE_THRESHOLD = 0.1

SYSTEM_PROMPT = """You are reviewing a SQL query for correctness, performance, and security.
Return exactly one JSON object with these keys:
- action_type: identify_issue, suggest_fix, approve, or request_more_context
- issue_category: syntax, performance, security, logic, or style (when relevant)
- issue_description: concise issue statement (when relevant)
- suggested_fix: corrected SQL or corrected fragment (when relevant)
- confidence: float between 0.0 and 1.0

Guidelines:
- Prefer identify_issue until you believe all important issues are covered.
- Use approve only when the query looks acceptable or all issues have been identified.
- Return ONLY valid JSON, no prose, no markdown fences.
"""

# ---------------------------------------------------------------------------
# Structured stdout logging — matches hackathon spec EXACTLY
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
# LLM interaction — fully wrapped in try/except
# ---------------------------------------------------------------------------


def extract_json(content: str) -> dict[str, Any]:
    stripped = content.strip()
    if stripped.startswith("```"):
        lines = [l for l in stripped.splitlines() if not l.startswith("```")]
        stripped = "\n".join(lines).strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"No JSON object found in: {content[:200]!r}")
    return json.loads(stripped[start : end + 1])


def choose_action(llm_client: Any, model_name: str, observation: Any) -> dict[str, Any]:
    """Ask LLM for an action. Returns a raw dict. NEVER raises."""
    try:
        obs_data = {
            "query": getattr(observation, "query", ""),
            "schema_info": getattr(observation, "schema_info", {}),
            "context": getattr(observation, "context", ""),
            "issues_found_so_far": [],
            "remaining_actions": getattr(observation, "remaining_actions", 0),
            "difficulty": getattr(observation, "difficulty", "unknown"),
            "feedback": getattr(observation, "feedback", ""),
        }

        # Safely serialize issues
        for i in getattr(observation, "issues_found_so_far", []):
            try:
                obs_data["issues_found_so_far"].append(
                    i.model_dump() if hasattr(i, "model_dump") else str(i)
                )
            except Exception:
                pass

        response = llm_client.chat.completions.create(
            model=model_name,
            temperature=0,
            max_tokens=300,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(obs_data, indent=2)},
            ],
        )
        content = response.choices[0].message.content or ""
        parsed = extract_json(content)
        if "action_type" not in parsed:
            parsed["action_type"] = "approve"
        return parsed

    except Exception as exc:
        print(f"[DEBUG] choose_action error: {exc}", flush=True)
        return {"action_type": "approve", "confidence": 0.1}


# ---------------------------------------------------------------------------
# Episode runner (async) — for from_docker_image connection
# ---------------------------------------------------------------------------


async def run_episode_async(
    env: Any, llm_client: Any, model_name: str, task_id: str
) -> None:
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=task_id, env=BENCHMARK, model=model_name)

    try:
        from sql_query_reviewer.models import SQLReviewAction

        result = await env.reset()

        for step_num in range(1, MAX_STEPS + 1):
            if result.done:
                break

            action_dict = choose_action(llm_client, model_name, result.observation)

            try:
                action = SQLReviewAction.model_validate(action_dict)
            except Exception:
                action = SQLReviewAction(action_type="approve", confidence=0.1)

            action_str = action.action_type
            if action.issue_description:
                action_str = f"{action.action_type}({action.issue_category})"

            try:
                result = await env.step(action)
            except Exception as step_err:
                print(f"[DEBUG] env.step error: {step_err}", flush=True)
                log_step(step=step_num, action=action_str, reward=0.0, done=True, error=str(step_err))
                rewards.append(0.0)
                steps_taken = step_num
                break

            reward = result.reward if result.reward is not None else 0.0
            rewards.append(reward)
            steps_taken = step_num
            error_msg = None
            if hasattr(result, "info") and result.info:
                error_msg = result.info.get("error")

            log_step(step=step_num, action=action_str, reward=reward, done=result.done, error=error_msg)

            if result.done:
                break

        # Final score
        try:
            state = await env.state()
            if hasattr(state, "final_score") and state.final_score is not None:
                score = state.final_score
            else:
                score = sum(rewards) / max(len(rewards), 1)
        except Exception:
            score = sum(rewards) / max(len(rewards), 1) if rewards else 0.0

        score = max(0.01, min(0.99, score))
        success = score >= SUCCESS_SCORE_THRESHOLD

    except Exception as exc:
        print(f"[DEBUG] Episode error: {exc}", flush=True)
        traceback.print_exc(file=sys.stdout)

    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)


# ---------------------------------------------------------------------------
# Episode runner (sync) — for direct HTTP connection
# ---------------------------------------------------------------------------


def run_episode(env: Any, llm_client: Any, model_name: str, task_id: str) -> None:
    """Public episode runner expected by tests.

    Uses the synchronous env interface: reset(task_id=...), step(...), state().
    """
    return run_episode_sync(env, llm_client, model_name, task_id)


def run_episode_sync(
    env: Any, llm_client: Any, model_name: str, task_id: str
) -> None:
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=task_id, env=BENCHMARK, model=model_name)

    try:
        from sql_query_reviewer.models import SQLReviewAction

        result = env.reset(task_id=task_id)

        for step_num in range(1, MAX_STEPS + 1):
            if result.done:
                break

            action_dict = choose_action(llm_client, model_name, result.observation)

            try:
                action = SQLReviewAction.model_validate(action_dict)
            except Exception:
                action = SQLReviewAction(action_type="approve", confidence=0.1)

            action_str = action.action_type
            if action.issue_description:
                action_str = f"{action.action_type}({action.issue_category})"

            try:
                result = env.step(action)
            except Exception as step_err:
                print(f"[DEBUG] env.step error: {step_err}", flush=True)
                log_step(step=step_num, action=action_str, reward=0.0, done=True, error=str(step_err))
                rewards.append(0.0)
                steps_taken = step_num
                break

            reward = result.reward if result.reward is not None else 0.0
            rewards.append(reward)
            steps_taken = step_num
            error_msg = None
            if hasattr(result, "info") and result.info:
                error_msg = result.info.get("error")

            log_step(step=step_num, action=action_str, reward=reward, done=result.done, error=error_msg)

            if result.done:
                break

        try:
            state = env.state()
            if hasattr(state, "final_score") and state.final_score is not None:
                score = state.final_score
            else:
                score = sum(rewards) / max(len(rewards), 1)
        except Exception:
            score = sum(rewards) / max(len(rewards), 1) if rewards else 0.0

        score = max(0.01, min(0.99, score))
        success = score >= SUCCESS_SCORE_THRESHOLD

    except Exception as exc:
        print(f"[DEBUG] Episode error: {exc}", flush=True)
        traceback.print_exc(file=sys.stdout)

    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)


# ---------------------------------------------------------------------------
# Main — tries Docker image first (validator), then HTTP (local dev)
# ---------------------------------------------------------------------------


async def async_main() -> int:
    # Build LLM client (even without key, don't crash — emit logs and exit)
    if not API_KEY:
        print("[DEBUG] WARNING: No API key found (HF_TOKEN / API_KEY / OPENAI_API_KEY)", flush=True)
        for tid in ["easy_001", "medium_001", "hard_001"]:
            log_start(task=tid, env=BENCHMARK, model=MODEL_NAME)
            log_end(success=False, steps=0, score=0.01, rewards=[])
        return 1

    llm_client = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)

    task_ids = tuple(
        tid.strip()
        for tid in os.getenv("TASK_IDS", "easy_001,medium_001,hard_001").split(",")
        if tid.strip()
    )

    env = None

    try:
        # ------------------------------------------------------------------
        # Method 1: from_docker_image (what the hackathon validator uses)
        # ------------------------------------------------------------------
        if IMAGE_NAME:
            print(f"[DEBUG] Connecting via Docker image: {IMAGE_NAME}", flush=True)
            try:
                from sql_query_reviewer.client import SQLReviewEnv
                env = await SQLReviewEnv.from_docker_image(IMAGE_NAME)
                print("[DEBUG] Docker connection OK", flush=True)
                for task_id in task_ids:
                    await run_episode_async(env, llm_client, MODEL_NAME, task_id)
                return 0
            except AttributeError:
                # from_docker_image not implemented in our client — try openenv-core
                print("[DEBUG] from_docker_image not in custom client, trying openenv generic", flush=True)
                try:
                    from openenv.core.env_client import GenericEnvClient
                    env = await GenericEnvClient.from_docker_image(IMAGE_NAME)
                    print("[DEBUG] GenericEnvClient Docker connection OK", flush=True)
                    for task_id in task_ids:
                        await run_episode_async(env, llm_client, MODEL_NAME, task_id)
                    return 0
                except Exception as exc2:
                    print(f"[DEBUG] GenericEnvClient also failed: {exc2}", flush=True)
            except Exception as exc:
                print(f"[DEBUG] Docker connection failed: {exc}", flush=True)

        # ------------------------------------------------------------------
        # Method 2: Async HTTP (fallback for local/URL-based testing)
        # ------------------------------------------------------------------
        print(f"[DEBUG] Connecting via URL: {ENV_BASE_URL}", flush=True)
        try:
            from sql_query_reviewer.client import SQLReviewEnv
            env = SQLReviewEnv(base_url=ENV_BASE_URL)
            await env.__aenter__()
            print("[DEBUG] Async URL connection OK", flush=True)
            for task_id in task_ids:
                await run_episode_async(env, llm_client, MODEL_NAME, task_id)
            return 0
        except Exception as exc:
            print(f"[DEBUG] Async URL failed: {exc}", flush=True)

        # ------------------------------------------------------------------
        # Method 3: Sync HTTP (last resort)
        # ------------------------------------------------------------------
        try:
            from sql_query_reviewer.client import SyncSQLReviewEnv
            sync_env = SyncSQLReviewEnv(base_url=ENV_BASE_URL)
            sync_env.__enter__()
            print("[DEBUG] Sync HTTP connection OK", flush=True)
            for task_id in task_ids:
                run_episode_sync(sync_env, llm_client, MODEL_NAME, task_id)
            sync_env.close()
            return 0
        except Exception as exc:
            print(f"[DEBUG] Sync HTTP also failed: {exc}", flush=True)

        # All methods failed — still emit valid log lines
        print("[DEBUG] All connection methods exhausted", flush=True)
        for task_id in task_ids:
            log_start(task=task_id, env=BENCHMARK, model=MODEL_NAME)
            log_end(success=False, steps=0, score=0.01, rewards=[])
        return 1

    except Exception as exc:
        print(f"[DEBUG] Fatal: {exc}", flush=True)
        traceback.print_exc(file=sys.stdout)
        return 1

    finally:
        if env is not None:
            try:
                await env.close()
            except Exception as close_err:
                print(f"[DEBUG] env.close() error: {close_err}", flush=True)


def main() -> int:
    return asyncio.run(async_main())


if __name__ == "__main__":
    raise SystemExit(main())
