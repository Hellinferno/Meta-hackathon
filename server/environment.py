from __future__ import annotations

import json
from pathlib import Path

from sql_query_reviewer.models import (
    IdentifiedIssue,
    SQLReviewAction,
    SQLReviewObservation,
    SQLReviewState,
    StepResult,
    TaskRecord,
)
from server.grader import grade_episode, match_issue, validate_fix
from server.reward import compute_reward


class SQLReviewEnvironment:
    def __init__(self, task_directory: Path | None = None) -> None:
        self.task_directory = task_directory or Path(__file__).resolve().parent.parent / "tasks"
        self.tasks = self._load_tasks()
        self.task_order = sorted(self.tasks)
        self.current_task: TaskRecord | None = None
        self.current_state: SQLReviewState | None = None
        self._reset_index = 0

    def available_task_ids(self) -> list[str]:
        return list(self.task_order)

    def reset(self, task_id: str | None = None) -> StepResult:
        selected_task_id = task_id or self._next_task_id()
        if selected_task_id not in self.tasks:
            raise ValueError(f"Unknown task_id: {selected_task_id}")

        self.current_task = self.tasks[selected_task_id]
        self.current_state = SQLReviewState(task_id=self.current_task.task_id)
        observation = self._build_observation(
            feedback="Review this SQL query and identify correctness, performance, or security issues."
        )
        return StepResult(observation=observation, reward=0.0, done=False, info={})

    def step(self, action: SQLReviewAction) -> StepResult:
        task = self._require_task()
        state = self._require_state()
        if state.done:
            raise RuntimeError("Episode already finished. Call reset() before taking more steps.")

        found_ids = {issue.issue_id for issue in state.issues_identified}
        reward = 0.0
        info: dict[str, object] = {}
        feedback = "No-op."
        state.step_count += 1

        if action.action_type == "identify_issue":
            duplicate_issue, duplicate_score = match_issue(action, task.ground_truth_issues, set())
            if duplicate_issue is not None and duplicate_issue.id in found_ids:
                reward = compute_reward(action, duplicate_issue, duplicate_issue=True)
                feedback = f"Issue '{duplicate_issue.id}' was already identified earlier in the episode."
                info = {"match_score": round(duplicate_score, 3), "match_type": "duplicate", "issue_id": duplicate_issue.id}
            else:
                matched_issue, score = match_issue(action, task.ground_truth_issues, found_ids)
                if matched_issue is None:
                    state.false_positive_count += 1
                    reward = compute_reward(action, None)
                    feedback = "No matching issue found for that description."
                    info = {"match_score": round(score, 3), "match_type": "none"}
                else:
                    fix_valid = validate_fix(action.suggested_fix, matched_issue)
                    state.issues_identified.append(
                        IdentifiedIssue(
                            issue_id=matched_issue.id,
                            category=matched_issue.category,
                            description=matched_issue.description,
                        )
                    )
                    reward = compute_reward(action, matched_issue, fix_valid=fix_valid, issues_found_count=len(state.issues_identified), schema_available=bool(task.schema_info))
                    remaining = len(task.ground_truth_issues) - len(state.issues_identified)
                    feedback = f"Matched {matched_issue.category} issue '{matched_issue.id}'. {remaining} issue(s) remaining."
                    info = {
                        "match_score": round(score, 3),
                        "match_type": "fuzzy",
                        "severity": matched_issue.severity,
                        "issue_id": matched_issue.id,
                        "all_issues_found": remaining == 0,
                    }
                    if fix_valid and action.suggested_fix:
                        state.fixes_suggested.append(action.suggested_fix)

        elif action.action_type == "suggest_fix":
            if not state.issues_identified:
                reward = compute_reward(action, None, has_previous_issue=False)
                feedback = "Identify an issue before suggesting a fix."
            else:
                last_issue_id = state.issues_identified[-1].issue_id
                last_issue = next(issue for issue in task.ground_truth_issues if issue.id == last_issue_id)
                fix_valid = validate_fix(action.suggested_fix, last_issue)
                reward = compute_reward(action, last_issue, fix_valid=fix_valid, has_previous_issue=True)
                feedback = "Fix accepted for the last identified issue." if fix_valid else "Suggested fix did not match the expected remediation."
                info = {"issue_id": last_issue.id, "fix_valid": fix_valid}
                if fix_valid and action.suggested_fix:
                    state.fixes_suggested.append(action.suggested_fix)

        elif action.action_type == "approve":
            remaining_unfound = len(task.ground_truth_issues) - len(found_ids)
            reward = compute_reward(action, None, remaining_unfound=remaining_unfound)
            state.approved = True
            state.done = True
            feedback = (
                "Query approved with full issue coverage."
                if remaining_unfound == 0
                else f"Query approved too early. {remaining_unfound} issue(s) were missed."
            )
            info = {"remaining_unfound": remaining_unfound}

        else:
            feedback = self._schema_feedback(task)
            reward = compute_reward(action, None, schema_available=bool(task.schema_info))
            info = {"context_shared": bool(task.schema_info)}

        state.total_reward += reward

        if state.step_count >= task.max_steps and not state.done:
            state.done = True
            feedback = f"{feedback} Maximum step count reached."

        if state.done:
            state.final_score = grade_episode(
                found_issue_ids={issue.issue_id for issue in state.issues_identified},
                ground_truth_issues=task.ground_truth_issues,
                total_steps=state.step_count,
                max_steps=task.max_steps,
                false_positive_count=state.false_positive_count,
            )
            info["final_score"] = state.final_score

        observation = self._build_observation(feedback=feedback)
        return StepResult(observation=observation, reward=reward, done=state.done, info=info)

    def state(self) -> SQLReviewState:
        return self._require_state().model_copy(deep=True)

    def _load_tasks(self) -> dict[str, TaskRecord]:
        tasks: dict[str, TaskRecord] = {}
        for file_path in sorted(self.task_directory.glob("*_tasks.json")):
            with file_path.open("r", encoding="utf-8") as handle:
                for raw_task in json.load(handle):
                    task = TaskRecord.model_validate(raw_task)
                    tasks[task.task_id] = task
        if not tasks:
            raise RuntimeError(f"No task files found in {self.task_directory}")
        return tasks

    def _next_task_id(self) -> str:
        task_id = self.task_order[self._reset_index % len(self.task_order)]
        self._reset_index += 1
        return task_id

    def _build_observation(self, feedback: str) -> SQLReviewObservation:
        task = self._require_task()
        state = self._require_state()
        remaining_actions = max(task.max_steps - state.step_count, 0)
        return SQLReviewObservation(
            query=task.query,
            schema_info=task.schema_info,
            context=task.context,
            issues_found_so_far=state.issues_identified,
            remaining_actions=remaining_actions,
            difficulty=task.difficulty,
            feedback=feedback,
        )

    def _schema_feedback(self, task: TaskRecord) -> str:
        if not task.schema_info:
            return "No additional schema context is available for this task."
        tables = ", ".join(sorted(task.schema_info))
        return f"Schema context available for: {tables}."

    def _require_task(self) -> TaskRecord:
        if self.current_task is None:
            raise RuntimeError("Environment has no active task. Call reset() first.")
        return self.current_task

    def _require_state(self) -> SQLReviewState:
        if self.current_state is None:
            raise RuntimeError("Environment has no active state. Call reset() first.")
        return self.current_state
