# 06 — API Contracts

## OpenEnv Standard Endpoints

### POST /reset
**Request:**
```json
{"task_id": "easy_001"}
```
**Response (StepResult):**
```json
{
  "observation": {
    "query": "SELCT * FORM users WEHRE id = 1",
    "schema_info": {"users": {"id": "INT PK", "name": "VARCHAR(255)", "email": "VARCHAR(255)"}},
    "context": "Fetch user by ID for profile page",
    "issues_found_so_far": [],
    "remaining_actions": 5,
    "difficulty": "easy",
    "feedback": "Review this SQL query and identify any issues."
  },
  "reward": 0.0,
  "done": false,
  "info": {}
}
```

### POST /step
**Request (Action):**
```json
{
  "action_type": "identify_issue",
  "issue_category": "syntax",
  "issue_description": "SELCT is misspelled, should be SELECT",
  "suggested_fix": "SELECT",
  "confidence": 0.95
}
```
**Response (StepResult):**
```json
{
  "observation": {
    "query": "SELCT * FORM users WEHRE id = 1",
    "schema_info": {"users": {"id": "INT PK", "name": "VARCHAR(255)", "email": "VARCHAR(255)"}},
    "context": "Fetch user by ID for profile page",
    "issues_found_so_far": [{"category": "syntax", "description": "SELCT should be SELECT"}],
    "remaining_actions": 4,
    "difficulty": "easy",
    "feedback": "Correct! SELCT is indeed a syntax error. 3 issues remaining."
  },
  "reward": 0.25,
  "done": false,
  "info": {"match_type": "exact", "severity": 0.3}
}
```

### GET /state
**Response (State):**
```json
{
  "task_id": "easy_001",
  "step_count": 1,
  "issues_identified": [{"category": "syntax", "description": "SELCT should be SELECT"}],
  "total_reward": 0.25,
  "done": false,
  "approved": false
}
```

## Pydantic Models

```python
class SQLReviewAction(Action):
    action_type: Literal["identify_issue", "suggest_fix", "approve", "request_more_context"]
    issue_category: Optional[Literal["syntax", "performance", "security", "logic", "style"]] = None
    issue_description: Optional[str] = None
    suggested_fix: Optional[str] = None
    confidence: float = 0.5

class SQLReviewObservation(Observation):
    query: str
    schema_info: Dict[str, Dict[str, str]]
    context: str
    issues_found_so_far: List[Dict[str, str]]
    remaining_actions: int
    difficulty: str
    feedback: str

class SQLReviewState(State):
    task_id: str
    step_count: int
    issues_identified: List[Dict[str, str]]
    total_reward: float
    done: bool
    approved: bool
```
