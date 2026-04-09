# 04 — System Architecture

## Components

```
┌─────────────────────────────────────────────┐
│                 HF Space                     │
│  ┌─────────────────────────────────────┐    │
│  │           FastAPI Server             │    │
│  │  (app.py — Uvicorn)                  │    │
│  │                                      │    │
│  │  POST /reset  → environment.reset()  │    │
│  │  POST /step   → environment.step()   │    │
│  │  GET  /state  → environment.state()  │    │
│  └──────────┬──────────────────────────┘    │
│             │                                │
│  ┌──────────▼──────────────────────────┐    │
│  │      SQLReviewEnvironment            │    │
│  │  - task_bank (easy/medium/hard JSON) │    │
│  │  - grader (deterministic scoring)    │    │
│  │  - reward_fn (per-step signals)      │    │
│  └─────────────────────────────────────┘    │
│                                              │
│  Dockerfile (Python 3.10-slim + deps)        │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│            inference.py (Client)             │
│  - OpenAI Client → LLM API                  │
│  - SQLReviewEnvClient → HF Space            │
│  - Structured stdout logging                 │
└─────────────────────────────────────────────┘
```

## Technology Stack
- **Runtime:** Python 3.10+
- **Framework:** FastAPI + Uvicorn
- **Models:** Pydantic v2
- **Container:** Docker (python:3.10-slim base)
- **Deployment:** Hugging Face Spaces (Docker SDK)
- **LLM Client:** OpenAI Python SDK
- **Environment SDK:** openenv-core

## Communication Protocol
- WebSocket at `/ws` for persistent sessions (OpenEnv standard)
- HTTP POST endpoints as fallback: `/reset`, `/step`
- HTTP GET: `/state`
- JSON request/response bodies matching typed Pydantic models

## Episode Lifecycle
1. Client calls `reset(task_id="easy_001")` → server loads task, returns initial observation
2. Client calls `step(action)` → server validates action, computes reward, returns observation
3. Repeat until `done=True` (all issues found, agent approves, or max_steps reached)
4. Client calls `close()` → server runs grader, returns final score
