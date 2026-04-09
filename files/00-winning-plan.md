# OpenEnv Hackathon — Winning Plan

**Participant:** Ravi (Solo)
**Deadline:** April 12, 2026, 11:59 PM IST
**Goal:** Top 3,000 out of 20,000 teams → Finale April 25–26

---

## Chosen Domain: **SQL Query Optimizer Review**

An environment where an AI agent reviews SQL queries for correctness, performance, and security issues — then suggests fixes. This scores high on real-world utility (30% weight), is novel in OpenEnv, has natural difficulty progression, and produces clear measurable rewards.

**Why this wins:**
- Every engineering team at Meta deals with SQL/data pipelines daily — maximum relevance
- Clear grading: each query has known issues, agent either finds them or doesn't → partial credit is natural
- Difficulty scales cleanly: syntax errors (easy) → performance anti-patterns (medium) → subtle injection vulnerabilities + schema-aware optimization (hard)
- Novel domain not seen in existing OpenEnv environments (creativity 10%)
- Deterministic grading with score variance (agents that find more issues score higher)

---

## Timeline

| When | What |
|---|---|
| **Apr 10, Morning** | Complete prep modules 1-4 on Colab, watch bootcamp recording |
| **Apr 10, Afternoon** | Install prerequisites, study sample inference script, study echo env code |
| **Apr 10, Evening** | Scaffold project with `openenv init`, define Pydantic models, implement core env logic |
| **Apr 11, Morning** | Implement 3 tasks (easy/medium/hard) with graders and reward functions |
| **Apr 11, Afternoon** | Write `inference.py`, test locally, iterate on reward shaping |
| **Apr 11, Evening** | Dockerize, deploy to HF Spaces, run pre-validation script |
| **Apr 12, Morning** | Write README, final testing, fix issues |
| **Apr 12, Afternoon** | Final pre-validation, submit |
| **Apr 12, Before 11:59 PM** | Verify HF Space is live and responding |

---

## Phase 0: Preparation (Today — First 3 Hours)

### Step 1: Complete Prep Course Modules
- Module 1: Interface basics (`reset()`, `step()`, `state()`)
- Module 2: Using existing environments, typed models
- Module 3: Deployment to HF Spaces with `openenv push`
- Module 4: **Building your own environment** — most critical, take detailed notes

### Step 2: Watch Bootcamp Recording
- Note tips from Ben Burtenshaw (HF) and Pulkit Aneja about what judges look for

### Step 3: Install Prerequisites
```bash
pip install openenv-core huggingface_hub openai pydantic
pip install docker  # or ensure Docker Desktop is running
huggingface-cli login
```

### Step 4: Study the Sample Inference Script
- Memorize the `[START]`, `[STEP]`, `[END]` stdout format
- Any deviation in field names/ordering = incorrect evaluation scoring

### Step 5: Study Existing Environments
- Clone `https://github.com/meta-pytorch/OpenEnv`
- Study `envs/echo_env/` structure: models.py, client.py, server/environment.py, server/app.py, server/Dockerfile

---

## Phase 1: Build the Environment

### Project Structure
```
sql-query-reviewer/
├── openenv.yaml
├── models.py              # Action, Observation, State Pydantic models
├── client.py              # EnvClient subclass
├── inference.py           # Baseline inference script (root!)
├── README.md
├── tasks/
│   ├── easy_tasks.json    # Syntax error queries
│   ├── medium_tasks.json  # Performance anti-pattern queries
│   └── hard_tasks.json    # Security + schema-aware optimization queries
└── server/
    ├── environment.py     # Core environment logic
    ├── grader.py          # Deterministic grading functions
    ├── app.py             # FastAPI server
    ├── Dockerfile
    └── requirements.txt
```

### Pydantic Models Design

**Observation:**
- `query`: The SQL query to review
- `schema_info`: Table/column definitions (for medium/hard tasks)
- `context`: What the query is supposed to do
- `issues_found_so_far`: List of issues already identified
- `remaining_actions`: How many review steps remain
- `difficulty`: easy | medium | hard

**Action:**
- `action_type`: "identify_issue" | "suggest_fix" | "approve" | "request_more_context"
- `issue_category`: "syntax" | "performance" | "security" | "logic" | "style"
- `issue_description`: Free text description of the issue
- `suggested_fix`: The corrected SQL (optional)
- `confidence`: Float 0.0-1.0

**Reward:** Float 0.0-1.0 with partial credit

### Three Tasks with Progressive Difficulty

**Task 1 — Easy: Syntax & Basic Logic Errors**
- Queries with missing keywords, wrong joins, typos in column names
- Agent identifies each error → 0.2 reward per correct identification
- Suggesting a valid fix → bonus 0.1 per fix
- Expected baseline score: 0.7-0.9

**Task 2 — Medium: Performance Anti-Patterns**
- SELECT *, missing indexes, N+1 patterns, unnecessary subqueries, missing WHERE clauses on large tables
- Requires understanding schema context
- Agent identifies anti-pattern + suggests optimization → partial credit
- Expected baseline score: 0.4-0.6

**Task 3 — Hard: Security Vulnerabilities + Schema-Aware Optimization**
- SQL injection vectors, privilege escalation, data leakage, plus complex optimization (query plan awareness)
- Requires multi-step reasoning about schema relationships
- Expected baseline score: 0.2-0.4

### Reward Function Design
- Per-step rewards (not just end-of-episode)
- Correct issue identification: +0.2 (scaled by issue severity)
- Valid fix suggestion: +0.1
- False positive (flagging non-issue): -0.1
- Missing critical issue at episode end: -0.15
- Approving a query with unfound issues: -0.2
- Smooth, informative signal throughout the trajectory

### Grader Design
- Each task has a ground-truth list of issues with categories and severity
- Grader compares agent's identified issues against ground truth using fuzzy matching on descriptions
- Score = (correctly_identified × severity_weight) / total_possible_score
- Deterministic: same agent output → same score every time
- Returns float in [0.0, 1.0]
- Never returns the same score for all inputs (variety of queries ensures variance)

---

## Phase 2: Inference Script

Key requirements:
- Named `inference.py` in root directory
- Uses OpenAI Client for all LLM calls
- Reads `API_BASE_URL`, `MODEL_NAME`, `HF_TOKEN` from env vars
- Emits `[START]`, `[STEP]`, `[END]` logs exactly per spec
- Completes in <20 minutes on 2 vCPU, 8GB RAM
- Reproducible scores

---

## Phase 3: Containerize & Deploy

```bash
# Build and test locally
docker build -t sql-query-reviewer ./server
docker run -p 8000:8000 sql-query-reviewer

# Verify endpoints
curl -X POST http://localhost:8000/reset -H "Content-Type: application/json" -d '{}'

# Deploy to HF Spaces
openenv push --repo-id ravi/sql-query-reviewer

# Verify deployed version
curl -X POST https://ravi-sql-query-reviewer.hf.space/reset
```

---

## Phase 4: Pre-Submission QA

Run pre-validation script:
```bash
./validate-submission.sh https://ravi-sql-query-reviewer.hf.space .
```

Checklist:
- [ ] HF Space deploys and responds to `/reset` with 200
- [ ] `openenv validate` passes
- [ ] Dockerfile builds cleanly
- [ ] Inference script runs without errors, produces scores
- [ ] 3+ tasks, each grader returns scores in 0.0-1.0 range
- [ ] Scores are reproducible across runs
- [ ] README is compelling and complete

---

## Winning Differentiators

1. **Real-world utility (30%)**: SQL review is something every data team needs — immediate value for the RL/agent community
2. **Score variance**: Different agent capabilities produce meaningfully different scores — a basic agent catches syntax errors but misses security issues
3. **Reward shaping**: Per-step partial credit signals, not binary end-of-episode
4. **Novelty**: No SQL review environment exists in OpenEnv yet
5. **Spec compliance**: Bulletproof adherence to every technical requirement — this alone eliminates most competitors
