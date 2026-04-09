# 08 — Reward & Grading Engine Spec

## Per-Step Reward Function

```python
def compute_reward(action, ground_truth_issues, already_found):
    if action.action_type == "identify_issue":
        match = fuzzy_match(action.issue_description, ground_truth_issues, already_found)
        if match:
            base = match["severity"]  # 0.1 - 1.0
            fix_bonus = 0.1 if action.suggested_fix and is_valid_fix(action.suggested_fix, match) else 0.0
            confidence_bonus = 0.05 * action.confidence if match else 0.0
            return min(base + fix_bonus + confidence_bonus, 0.4)  # cap per-step
        else:
            return -0.1  # false positive penalty

    elif action.action_type == "approve":
        unfound = len(ground_truth_issues) - len(already_found)
        if unfound == 0:
            return 0.2  # correct approval
        else:
            return -0.15 * unfound  # penalty per missed issue

    elif action.action_type == "suggest_fix":
        if not already_found:
            return -0.05  # fixing without identifying first
        last_issue = already_found[-1]
        if is_valid_fix(action.suggested_fix, last_issue):
            return 0.1
        return 0.0

    elif action.action_type == "request_more_context":
        return 0.0  # neutral — no reward, no penalty

    return 0.0
```

## Fuzzy Matching Algorithm

```python
def fuzzy_match(agent_description, ground_truth_issues, already_found):
    """Match agent's issue description to a ground truth issue."""
    best_match = None
    best_score = 0.0
    
    for issue in ground_truth_issues:
        if issue in already_found:
            continue
        # Keyword overlap score
        agent_words = set(agent_description.lower().split())
        truth_words = set(issue["keywords"])
        overlap = len(agent_words & truth_words) / max(len(truth_words), 1)
        # Category match bonus
        category_bonus = 0.3 if action.issue_category == issue["category"] else 0.0
        score = overlap + category_bonus
        if score > best_score and score > 0.3:  # threshold
            best_score = score
            best_match = issue
    
    return best_match
```

## End-of-Episode Grader

```python
def grade_episode(issues_found, ground_truth_issues, total_steps, max_steps):
    """Deterministic grader returning float in [0.0, 1.0]."""
    if not ground_truth_issues:
        return 1.0 if not issues_found else 0.5
    
    total_severity = sum(i["severity"] for i in ground_truth_issues)
    found_severity = sum(i["severity"] for i in issues_found if i in matched_ground_truth)
    
    coverage_score = found_severity / total_severity  # 0.0 - 1.0
    efficiency_bonus = max(0, 0.1 * (1 - total_steps / max_steps))  # reward fewer steps
    false_positive_penalty = 0.05 * count_false_positives(issues_found, ground_truth_issues)
    
    score = coverage_score + efficiency_bonus - false_positive_penalty
    return max(0.0, min(1.0, score))
```

## Score Variance Guarantee
- Easy tasks: 5 different queries with 2-5 issues each → scores range from 0.4 to 1.0
- Medium tasks: different anti-patterns → scores range from 0.2 to 0.8
- Hard tasks: varied security issues → scores range from 0.0 to 0.6
- A grader that always returns the same score = instant DQ. Our design inherently prevents this because different queries have different ground truth issues.
