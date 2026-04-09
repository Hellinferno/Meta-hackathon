# SQL Query Reviewer — OpenEnv Environment

An AI agent environment for reviewing SQL queries for correctness, performance, and security issues.

## Why This Matters

Every engineering team reviews SQL queries daily — in code reviews, migration scripts, ETL pipelines, and security audits. This environment lets you train and evaluate AI agents on a task that directly maps to real engineering workflows. Unlike toy benchmarks, the queries here reflect genuine patterns found in production codebases: misspelled keywords, N+1 anti-patterns, missing indexes, SQL injection vectors, and schema-aware optimization opportunities.

## Environment Overview

The agent receives a SQL query (plus optional schema context) and must identify issues through a multi-step review process. It earns rewards for correctly flagging problems and suggesting fixes, while being penalized for false positives or approving buggy queries.

## Action Space

| Action Type | Description |
|---|---|
| `identify_issue` | Flag a specific issue with category and description |
| `suggest_fix` | Propose corrected SQL for a previously identified issue |
| `approve` | Mark the query as acceptable (ends episode) |
| `request_more_context` | Ask for additional schema information |

**Fields:** `action_type`, `issue_category` (syntax/performance/security/logic/style), `issue_description`, `suggested_fix`, `confidence` (0.0-1.0)

## Observation Space

| Field | Type | Description |
|---|---|---|
| `query` | str | The SQL query under review |
| `schema_info` | dict | Table/column definitions (richer for harder tasks) |
| `context` | str | What the query is supposed to do |
| `issues_found_so_far` | list | Previously identified issues this episode |
| `remaining_actions` | int | Steps left before episode ends |
| `difficulty` | str | easy, medium, or hard |
| `feedback` | str | Result of last action |

## Tasks

### Task 1: Syntax Error Detection (Easy)
Queries with obvious typos, missing keywords, wrong column names. A baseline agent should score **0.7-0.9**.

### Task 2: Performance Anti-Pattern Review (Medium)
Queries with SELECT *, missing indexes, correlated subqueries, unbounded queries. Requires schema awareness. Expected score: **0.4-0.6**.

### Task 3: Security & Optimization Audit (Hard)
SQL injection vectors, privilege escalation, data leakage, complex optimization. Requires multi-step reasoning. Expected score: **0.2-0.4**.

## Reward Design
- Per-step partial credit (not binary end-of-episode)
- Correct issue identification: +0.1 to +0.4 (scaled by severity)
- Valid fix suggestion: +0.1 bonus
- False positive: -0.1 penalty
- Approving a query with unfound issues: -0.15 per missed issue
- Correct approval of clean query: +0.2

## Setup

```bash
# Install
pip install openenv-core
pip install git+https://huggingface.co/spaces/ravi/sql-query-reviewer

# Use
from sql_query_reviewer import SQLReviewEnv, SQLReviewAction

with SQLReviewEnv(base_url="https://ravi-sql-query-reviewer.hf.space").sync() as env:
    result = env.reset()
    result = env.step(SQLReviewAction(
        action_type="identify_issue",
        issue_category="syntax",
        issue_description="SELCT should be SELECT"
    ))
    print(result.observation.feedback)
```

## Docker

```bash
docker build -t sql-query-reviewer ./server
docker run -p 8000:8000 sql-query-reviewer
```

## Baseline Scores

| Task | Difficulty | Baseline Score |
|---|---|---|
| Syntax Error Detection | Easy | ~0.82 |
| Performance Anti-Pattern Review | Medium | ~0.51 |
| Security & Optimization Audit | Hard | ~0.29 |

## Author
**Ravi** — Solo participant, Meta PyTorch OpenEnv Hackathon 2026
