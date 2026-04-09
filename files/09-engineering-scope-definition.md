# 09 — Engineering Scope Definition

## In Scope (Must Build)
1. **Environment server** — `environment.py` with `reset()`, `step()`, `state()`
2. **Pydantic models** — `models.py` with typed Action, Observation, State
3. **Client** — `client.py` with EnvClient subclass
4. **Task bank** — 15 SQL queries (5 easy, 5 medium, 5 hard) with ground truth
5. **Grader** — Deterministic scoring function per task
6. **Reward function** — Per-step partial credit with penalties
7. **Inference script** — `inference.py` using OpenAI Client
8. **Dockerfile** — Working container that builds and runs
9. **HF Space deployment** — Live, tagged with `openenv`
10. **README** — Complete documentation
11. **openenv.yaml** — Valid metadata manifest

## Out of Scope (Don't Build)
- Real database execution (all analysis is pattern-matching based)
- Custom LLM fine-tuning
- Web UI beyond OpenEnv's built-in web interface
- Multiple language SQL dialects (stick to standard SQL)
- Integration tests against real databases

## Effort Estimates

| Component | Hours | Priority |
|---|---|---|
| Prep course + bootcamp | 3.0 | P0 |
| Task bank creation (15 queries + ground truth) | 2.5 | P0 |
| Pydantic models | 0.5 | P0 |
| Environment logic (reset/step/state) | 3.0 | P0 |
| Grader + reward function | 2.0 | P0 |
| Inference script | 1.5 | P0 |
| Dockerfile + local testing | 1.0 | P0 |
| HF Space deployment | 0.5 | P0 |
| README | 1.0 | P0 |
| Pre-validation + bug fixes | 2.0 | P0 |
| **Total** | **~17 hours** | |

Fits within the 2-day window with buffer for debugging.
