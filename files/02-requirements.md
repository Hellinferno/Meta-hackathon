# 02 — Requirements Specification

## Functional Requirements

### FR-1: Real-World Task Simulation
- Simulates SQL query review — a task humans do daily in engineering teams
- No games, no toys — purely professional/practical domain

### FR-2: OpenEnv Spec Compliance
- Typed Pydantic models for Observation, Action, State
- `step(action)` → returns observation, reward, done, info
- `reset()` → returns initial observation
- `state()` → returns current internal state
- Valid `openenv.yaml` with metadata
- Passes `openenv validate`

### FR-3: Minimum 3 Tasks with Agent Graders
- **Task 1 (Easy):** Syntax & basic logic errors — expected agent score 0.7-0.9
- **Task 2 (Medium):** Performance anti-patterns — expected agent score 0.4-0.6
- **Task 3 (Hard):** Security vulnerabilities + schema-aware optimization — expected agent score 0.2-0.4
- Each grader: deterministic, returns float in [0.0, 1.0], reproducible

### FR-4: Meaningful Reward Function
- Per-step rewards (not just end-of-episode binary)
- Partial credit for partial issue identification
- Penalties for false positives and missed critical issues
- Smooth signal that guides learning

### FR-5: Baseline Inference Script
- Named `inference.py` in project root
- Uses OpenAI Client for LLM calls
- Reads `API_BASE_URL`, `MODEL_NAME`, `HF_TOKEN` from env vars
- Emits `[START]`, `[STEP]`, `[END]` structured stdout logs
- Produces reproducible baseline scores on all 3 tasks

## Non-Functional Requirements

### NFR-1: Deploys to Hugging Face Space
- Containerized HF Space tagged with `openenv`
- Returns 200 and responds to `/reset` POST

### NFR-2: Containerized Execution
- Working Dockerfile
- Builds with `docker build`, runs with `docker run`
- Starts cleanly, responds to HTTP requests

### NFR-3: Infrastructure Constraints
- Inference script runtime < 20 minutes
- Runs on 2 vCPU, 8GB RAM machine

### NFR-4: Documentation
- README with: environment description, motivation, action/observation space definitions, task descriptions with difficulty, setup instructions, baseline scores

## Disqualification Criteria (Must Avoid)
- ❌ Environment does not deploy or respond
- ❌ Plagiarized or trivially modified existing environments
- ❌ Graders that always return the same score
- ❌ No baseline inference script
