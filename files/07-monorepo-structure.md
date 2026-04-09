# 07 — Monorepo Structure

```
sql-query-reviewer/
│
├── openenv.yaml                 # Environment metadata manifest
├── models.py                    # Pydantic: SQLReviewAction, SQLReviewObservation, SQLReviewState
├── client.py                    # EnvClient subclass for external consumers
├── inference.py                 # MANDATORY: Baseline inference script (root directory!)
├── README.md                    # Environment documentation
├── pyproject.toml               # Package config
│
├── tasks/
│   ├── easy_tasks.json          # 5 syntax/logic error queries
│   ├── medium_tasks.json        # 5 performance anti-pattern queries
│   └── hard_tasks.json          # 5 security + optimization queries
│
└── server/
    ├── __init__.py
    ├── environment.py           # SQLReviewEnvironment(Environment) — core logic
    ├── grader.py                # Deterministic grading: fuzzy match agent output vs ground truth
    ├── reward.py                # Per-step reward computation
    ├── app.py                   # FastAPI server (create_app with routes)
    ├── Dockerfile               # Python 3.10-slim, install deps, expose port
    └── requirements.txt         # openenv-core, fastapi, uvicorn, pydantic
```

## Key Files Explained

| File | Purpose | Critical? |
|---|---|---|
| `openenv.yaml` | Metadata: name, description, author, tasks list | Yes — validated by `openenv validate` |
| `models.py` | Typed Action/Observation/State contracts | Yes — spec compliance |
| `inference.py` | Baseline agent using OpenAI Client | Yes — DQ if missing |
| `server/environment.py` | `reset()`, `step()`, `state()` implementation | Yes — core logic |
| `server/grader.py` | Score computation per task | Yes — must return 0.0-1.0 |
| `server/Dockerfile` | Container definition | Yes — must build cleanly |
| `README.md` | Human-readable documentation | Yes — judges read this first |

## openenv.yaml

```yaml
name: sql-query-reviewer
description: "AI agent reviews SQL queries for correctness, performance, and security"
author: ravi
version: "1.0.0"
tags:
  - openenv
  - sql
  - code-review
  - security
tasks:
  - id: easy_syntax
    name: "Syntax Error Detection"
    difficulty: easy
    description: "Find and fix obvious SQL syntax errors"
  - id: medium_performance
    name: "Performance Anti-Pattern Review"
    difficulty: medium
    description: "Identify performance issues requiring schema awareness"
  - id: hard_security
    name: "Security & Optimization Audit"
    difficulty: hard
    description: "Find SQL injection vectors and complex optimization opportunities"
```
