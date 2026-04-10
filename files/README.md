---
title: SQL Query Reviewer
colorFrom: blue
colorTo: green
sdk: docker
app_port: 8000
pinned: false
tags:
  - openenv
---

# SQL Query Reviewer

An OpenEnv environment where an AI agent reviews SQL queries for correctness, performance, and security — the same task thousands of engineers perform every day in code reviews, migration scripts, and ETL audits.

## Why This Matters

SQL bugs are among the most common and costly defects in production systems. A misplaced keyword breaks an API, a missing index degrades latency by 100x, and an unsanitized input opens a door to data exfiltration. Today these defects are caught by human reviewers who spend hours on repetitive pattern matching. This environment provides a standardized benchmark to train and evaluate AI agents that can automate this critical workflow — directly useful for developer tools, IDE integrations, and automated code review systems.

## What The Environment Does

Each episode gives the agent:

- a SQL query (with realistic bugs drawn from production patterns)
- schema context when it matters (table definitions, column types, constraints)
- a short explanation of the query's intended purpose

The agent responds step by step with one of four actions:

| Action | Description |
|---|---|
| `identify_issue` | Flag a correctness, performance, or security problem |
| `suggest_fix` | Propose corrected SQL for a previously identified issue |
| `approve` | Mark the query as acceptable (ends episode) |
| `request_more_context` | Ask for additional schema information |

## Reward Design

Rewards are deterministic and shaped for partial progress throughout the trajectory:

- **Correct issue identification**: +0.10 to +0.35 scaled by issue severity
- **Valid fix suggestion**: +0.08 to +0.10 bonus
- **Confidence bonus**: up to +0.05 for high-confidence correct identifications
- **False positive**: −0.10 penalty
- **Duplicate identification**: −0.02 penalty
- **Approving with missed issues**: −0.15 per missed issue
- **Complete correct approval**: +0.20

## Task Bank

The environment ships with **15 tasks** across three difficulty levels:

| Difficulty | Count | Examples | Expected Baseline Score |
|---|---|---|---|
| Easy | 5 | Misspelled keywords, missing FROM, = NULL vs IS NULL | ~0.75–0.90 |
| Medium | 5 | SELECT *, missing indexes, correlated subqueries, unbounded queries | ~0.40–0.60 |
| Hard | 5 | SQL injection, privilege escalation, PII leakage, self-join optimization | ~0.20–0.40 |

Task data: `tasks/easy_tasks.json`, `tasks/medium_tasks.json`, `tasks/hard_tasks.json`

## Action & Observation Spaces

**Action** (`SQLReviewAction`):
- `action_type`: identify_issue | suggest_fix | approve | request_more_context
- `issue_category`: syntax | performance | security | logic | style
- `issue_description`: concise statement of the problem
- `suggested_fix`: corrected SQL fragment
- `confidence`: float 0.0–1.0

**Observation** (`SQLReviewObservation`):
- `query`: the full SQL query text
- `schema_info`: dict of table → column definitions
- `context`: natural language description of query intent
- `issues_found_so_far`: previously identified issues this episode
- `remaining_actions`: steps left before episode ends
- `difficulty`: easy | medium | hard
- `feedback`: result of last action

## Repository Layout

```
.
├── openenv.yaml
├── models.py
├── client.py
├── inference.py          ← baseline agent (root directory)
├── Dockerfile
├── sql_query_reviewer/   ← typed models and client package
├── server/               ← FastAPI environment server
│   ├── environment.py    ← reset(), step(), state()
│   ├── grader.py         ← deterministic scoring
│   ├── reward.py         ← per-step reward computation
│   └── app.py            ← HTTP routes
├── tasks/                ← 15 SQL query tasks (JSON)
└── tests/                ← pytest suite
```

## Local Development

```bash
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -e .[dev]
uvicorn server.app:app --reload --port 8000
```

Test the API:
```bash
curl -X POST http://localhost:8000/reset -H "Content-Type: application/json" -d '{"task_id":"easy_001"}'
curl http://localhost:8000/state
pytest
```

## Docker

```bash
docker build -t sql-query-reviewer .
docker run -p 8000:8000 sql-query-reviewer
```

## Inference

```bash
export ENV_BASE_URL=http://localhost:8000
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
export HF_TOKEN=hf_xxx
python inference.py
```

The script emits structured `[START]`, `[STEP]`, `[END]` logs per the OpenEnv spec.

## Hugging Face Spaces

This repo is Space-ready: HF YAML front matter in README, root Dockerfile, API on port 8000. Deploy with:

```bash
git remote add hf https://huggingface.co/spaces/<username>/sql-query-reviewer
git push hf main
```

## Usage Example

```python
from sql_query_reviewer import SQLReviewAction, SQLReviewEnv

with SQLReviewEnv(base_url="https://hellinferno-sql-query-reviewer.hf.space").sync() as env:
    result = env.reset(task_id="easy_001")
    result = env.step(SQLReviewAction(
        action_type="identify_issue",
        issue_category="syntax",
        issue_description="SELCT is misspelled and should be SELECT",
        suggested_fix="SELECT * FROM users WHERE id = 1;",
        confidence=0.98,
    ))
    print(result.reward)
    print(result.observation.feedback)
```

## Author

**Hellinferno** — Solo participant, Meta PyTorch OpenEnv Hackathon 2026
