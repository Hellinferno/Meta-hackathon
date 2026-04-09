---
title: SQL Query Reviewer
colorFrom: blue
colorTo: green
sdk: docker
app_port: 8000
pinned: false
---

# SQL Query Reviewer

`Meta-hackathon` is the GitHub source repo for `sql-query-reviewer`, an OpenEnv-style environment where an agent reviews SQL queries for correctness, performance, and security issues.

The same repository is designed to work in both places:
- GitHub is the canonical source, CI surface, and collaboration home.
- Hugging Face Spaces runs the Dockerized FastAPI environment directly from this repo layout.

## What The Environment Does

Each episode gives the agent:
- a SQL query
- schema context when it matters
- a short explanation of the query's intended purpose

The agent responds step by step with one of four actions:
- `identify_issue`
- `suggest_fix`
- `approve`
- `request_more_context`

Rewards are deterministic and shaped for partial progress:
- correct issue identification earns severity-weighted reward
- valid fixes earn bonus reward
- false positives are penalized
- approving with missed issues is penalized

## Repository Layout

```text
.
|-- .github/workflows/
|-- client.py
|-- Dockerfile
|-- inference.py
|-- models.py
|-- openenv.yaml
|-- pyproject.toml
|-- server/
|-- sql_query_reviewer/
|-- tasks/
`-- tests/
```

## Task Bank

The environment ships with 15 tasks:
- 5 easy syntax and basic logic reviews
- 5 medium schema-aware performance reviews
- 5 hard security and advanced optimization reviews

Task data lives in:
- `tasks/easy_tasks.json`
- `tasks/medium_tasks.json`
- `tasks/hard_tasks.json`

## Local Development

Install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e .[dev]
```

Run the API locally:

```bash
uvicorn server.app:app --reload --port 8000
```

Smoke-test the API:

```bash
curl -X POST http://localhost:8000/reset -H "Content-Type: application/json" -d "{\"task_id\":\"easy_001\"}"
curl http://localhost:8000/state
```

Run tests:

```bash
pytest
```

Build the container:

```bash
docker build -t sql-query-reviewer .
docker run -p 8000:8000 sql-query-reviewer
```

## Inference Script

`inference.py` uses the OpenAI Python client against any OpenAI-compatible endpoint.

Expected environment variables:

```bash
set ENV_BASE_URL=http://localhost:8000
set API_BASE_URL=https://router.huggingface.co/v1
set MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
set HF_TOKEN=hf_xxx
python inference.py
```

The script emits structured logs using:
- `[START]`
- `[STEP]`
- `[END]`

## Hugging Face Spaces

This repo is Space-ready because:
- the README starts with Hugging Face YAML front matter
- the repo includes a root `Dockerfile`
- the API listens on port `8000`

To deploy manually from a local machine with git:

```bash
git remote add hf https://huggingface.co/spaces/<hf-username>/sql-query-reviewer
git push hf main
```

If you install the OpenEnv CLI, you can also use:

```bash
python -m pip install "git+https://github.com/meta-pytorch/OpenEnv.git"
openenv push --repo-id <hf-username>/sql-query-reviewer
```

## GitHub Actions

CI runs tests and a Docker build on pushes and pull requests.

The Hugging Face sync workflow expects:
- GitHub secret `HF_TOKEN`
- optional GitHub variable `HF_SPACE_ID`

If `HF_SPACE_ID` is not set, the workflow defaults to:

```text
<github-repository-owner>/sql-query-reviewer
```

## Usage Example

```python
from sql_query_reviewer import SQLReviewAction, SQLReviewEnv

with SQLReviewEnv(base_url="http://localhost:8000").sync() as env:
    result = env.reset(task_id="easy_001")
    result = env.step(
        SQLReviewAction(
            action_type="identify_issue",
            issue_category="syntax",
            issue_description="SELCT is misspelled and should be SELECT",
            suggested_fix="SELECT * FROM users WHERE id = 1;",
            confidence=0.98,
        )
    )
    print(result.reward)
    print(result.observation.feedback)
```
