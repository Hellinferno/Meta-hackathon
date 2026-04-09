# 10 — Development Phases

## Phase 1: Learn (Apr 10, 9 AM – 12 PM)
- [ ] Complete Module 1: Interface basics
- [ ] Complete Module 2: Using existing environments
- [ ] Complete Module 3: Deployment to HF Spaces
- [ ] Complete Module 4: Building your own environment
- [ ] Watch bootcamp recording, note judge preferences
- [ ] Study sample inference script format

## Phase 2: Scaffold (Apr 10, 12 PM – 2 PM)
- [ ] `pip install openenv-core huggingface_hub openai`
- [ ] `openenv init sql-query-reviewer`
- [ ] Clone and study echo env for reference
- [ ] Set up project structure per 07-monorepo-structure.md

## Phase 3: Core Build (Apr 10, 2 PM – Apr 11, 12 PM)
- [ ] Write `models.py` — Action, Observation, State
- [ ] Create task bank — 5 easy, 5 medium, 5 hard queries with ground truth
- [ ] Implement `environment.py` — reset(), step(), state()
- [ ] Implement `grader.py` — deterministic scoring
- [ ] Implement `reward.py` — per-step reward computation
- [ ] Implement fuzzy matching for issue identification
- [ ] Write `app.py` — FastAPI routes
- [ ] Local testing: `uv run server` → test all endpoints manually

## Phase 4: Inference (Apr 11, 12 PM – 3 PM)
- [ ] Write `inference.py` following sample script format exactly
- [ ] System prompt design for SQL review agent
- [ ] Test with free HF Inference API
- [ ] Verify `[START]`, `[STEP]`, `[END]` output format
- [ ] Run 3x to verify reproducible scores

## Phase 5: Containerize & Deploy (Apr 11, 3 PM – 6 PM)
- [ ] Write Dockerfile (python:3.10-slim base)
- [ ] `docker build -t sql-query-reviewer ./server`
- [ ] `docker run -p 8000:8000 sql-query-reviewer`
- [ ] Test `/reset`, `/step`, `/state` against running container
- [ ] `openenv push --repo-id ravi/sql-query-reviewer`
- [ ] Verify HF Space returns 200 on `/reset`

## Phase 6: Polish & Submit (Apr 11, 6 PM – Apr 12, 11:59 PM)
- [ ] Write compelling README
- [ ] Run `openenv validate`
- [ ] Run `validate-submission.sh`
- [ ] Fix any issues
- [ ] Submit early, iterate if time permits
- [ ] Final verification: HF Space live and responding
