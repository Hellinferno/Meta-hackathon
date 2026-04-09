# Project Design

## Design Principles

1. **Spec compliance first, creativity second.** Most teams will fail on automated validation. Perfect adherence to the OpenEnv spec is the highest-ROI activity.

2. **Reward shaping is the differentiator.** Binary end-of-episode rewards are common. Per-step, severity-weighted, partial-credit rewards are what separate top submissions.

3. **Score variance is mandatory.** The environment must produce different scores for different agent capabilities. Our design inherently ensures this: different queries have different issues, so no two episodes produce identical scores.

4. **Domain authenticity wins the 30%.** Real-world utility is the highest-weighted criterion. SQL review is a task every Meta engineer knows and values. The task bank should contain queries that feel like real code review findings, not synthetic puzzles.

## Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Domain | SQL Query Review | Universal relevance, clear grading, natural difficulty progression |
| Task count | 15 queries (5/5/5) | Well above minimum 3, shows depth |
| Matching | Fuzzy keyword matching | Robust to LLM phrasing variation while staying deterministic |
| Reward | Per-step partial credit | Provides learning signal throughout trajectory |
| Episode length | 3-8 steps | Short enough for 20-min inference limit across all tasks |
| Grader | Severity-weighted coverage | Rewards finding critical issues more than trivial ones |

## Risk Mitigation

| Risk | Mitigation |
|---|---|
| Fuzzy matching too loose → inflated scores | Require 30% keyword overlap threshold + category match |
| Fuzzy matching too strict → no agent can score | Include broad keywords list, test with actual LLM output |
| Inference timeout | 15 queries × 5-8 steps × ~3s per LLM call = ~6 min. Well under 20 min. |
| Docker build fails on HF | Use minimal dependencies, test Dockerfile locally first |
| Grader returns same score | Impossible with varied queries — but verify during testing |

## What Judges Will See

1. **README** — Clear, compelling, explains why SQL review matters and how the env works
2. **HF Space** — Live, responds instantly to `/reset`
3. **Code** — Clean, well-structured, typed models, deterministic graders
4. **Scores** — Meaningful variance: easy ~0.8, medium ~0.5, hard ~0.3
5. **Novelty** — No existing SQL review env in OpenEnv ecosystem
