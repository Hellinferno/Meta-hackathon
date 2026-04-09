# 03 — Information Architecture

## Data Flow

```
[Task JSON] → reset() → [Observation: query + schema + context]
                              ↓
                    Agent decides action
                              ↓
                step(Action) → [Observation + Reward + Done]
                              ↓
                    (repeat until done or max_steps)
                              ↓
                close() → Grader computes final score
```

## Task Data Structure

Each task is a JSON object:
```json
{
  "task_id": "easy_001",
  "difficulty": "easy",
  "query": "SELCT * FORM users WEHRE id = 1",
  "schema": {
    "users": {"id": "INT PRIMARY KEY", "name": "VARCHAR(255)", "email": "VARCHAR(255)"}
  },
  "context": "Fetch user by ID for profile page",
  "ground_truth_issues": [
    {"category": "syntax", "description": "SELCT should be SELECT", "severity": 0.3, "fix": "SELECT"},
    {"category": "syntax", "description": "FORM should be FROM", "severity": 0.3, "fix": "FROM"},
    {"category": "syntax", "description": "WEHRE should be WHERE", "severity": 0.3, "fix": "WHERE"},
    {"category": "performance", "description": "SELECT * fetches unnecessary columns", "severity": 0.1, "fix": "SELECT id, name, email"}
  ],
  "max_steps": 5
}
```

## State Management

| Field | Type | Description |
|---|---|---|
| `task_id` | str | Current task identifier |
| `query` | str | The SQL query under review |
| `issues_identified` | list | Issues the agent has found so far |
| `fixes_suggested` | list | Fixes the agent has proposed |
| `step_count` | int | Current step number |
| `total_reward` | float | Accumulated reward |
| `done` | bool | Whether episode is complete |
| `approved` | bool | Whether agent approved the query |

## Observation Space
- `query`: The full SQL query text
- `schema_info`: Dict of table → column definitions (empty for easy tasks)
- `context`: Natural language description of query intent
- `issues_found_so_far`: List of previously identified issues in this episode
- `remaining_actions`: Max steps minus current step
- `difficulty`: "easy" | "medium" | "hard"
- `feedback`: Result of last action ("correct identification", "false positive", "already identified", etc.)

## Action Space
- `action_type`: enum — "identify_issue" | "suggest_fix" | "approve" | "request_more_context"
- `issue_category`: enum — "syntax" | "performance" | "security" | "logic" | "style"
- `issue_description`: str — what the agent thinks is wrong
- `suggested_fix`: str (optional) — corrected SQL fragment
- `confidence`: float 0.0-1.0
