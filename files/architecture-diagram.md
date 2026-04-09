# Architecture Diagram

## High-Level Flow

```
┌──────────────┐     ┌───────────────────────────────────┐
│              │     │        HF Space (Docker)           │
│  inference.py│     │                                    │
│  (Agent)     │     │  ┌──────────────────────────┐     │
│              │ WS  │  │    FastAPI Server         │     │
│  ┌────────┐  ├────►│  │    (app.py)               │     │
│  │ OpenAI │  │     │  │                           │     │
│  │ Client │  │     │  │  /reset → load task       │     │
│  │   ↕    │  │◄────┤  │  /step  → grade action    │     │
│  │  LLM   │  │     │  │  /state → return state    │     │
│  └────────┘  │     │  └──────────┬───────────────┘     │
│              │     │             │                      │
│  stdout:     │     │  ┌──────────▼───────────────┐     │
│  [START]     │     │  │  SQLReviewEnvironment     │     │
│  [STEP]      │     │  │  - task_bank (JSON)       │     │
│  [END]       │     │  │  - fuzzy_matcher          │     │
│              │     │  │  - reward_fn              │     │
└──────────────┘     │  │  - grader                 │     │
                     │  └──────────────────────────┘     │
                     └───────────────────────────────────┘
```

## Episode Sequence

```
Agent                          Environment
  │                                │
  │──── reset(task_id) ──────────►│  Load task from JSON
  │◄─── observation ──────────────│  Return query + schema + context
  │                                │
  │──── step(identify_issue) ────►│  Fuzzy match vs ground truth
  │◄─── obs + reward + done ──────│  Return feedback + reward
  │                                │
  │──── step(suggest_fix) ───────►│  Validate fix
  │◄─── obs + reward + done ──────│  Return feedback + reward
  │                                │
  │──── step(approve) ───────────►│  Check remaining issues
  │◄─── obs + reward + done=true──│  Episode ends
  │                                │
  │──── close() ─────────────────►│  Run grader → final score
  │◄─── final_score ──────────────│
  │                                │
```

## Evaluation Pipeline (Hackathon Judges)

```
Phase 1: Automated Validation
  └─ HF Space responds? → openenv validate? → Docker builds? → inference.py runs? → 3+ tasks?

Phase 2: Agentic Evaluation
  └─ Run Nemotron 3 Super against all envs → check score variance

Phase 3: Human Review
  └─ Meta + HF engineers review for utility, creativity, exploit checks
```
