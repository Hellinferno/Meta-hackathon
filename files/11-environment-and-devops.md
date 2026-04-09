# 11 — Environment & DevOps

## Local Development Setup

```bash
# Python environment
python3.10 -m venv .venv
source .venv/bin/activate
pip install openenv-core fastapi uvicorn pydantic openai huggingface_hub

# Run locally
cd server && uvicorn app:app --reload --port 8000

# Test endpoints
curl -X POST http://localhost:8000/reset -H "Content-Type: application/json" -d '{"task_id": "easy_001"}'
```

## Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY models.py .
COPY tasks/ ./tasks/
COPY server/ ./server/
COPY openenv.yaml .

EXPOSE 8000

CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## server/requirements.txt

```
openenv-core>=0.1.0
fastapi>=0.100.0
uvicorn>=0.23.0
pydantic>=2.0.0
```

## HF Space Deployment

```bash
# Login
huggingface-cli login

# Deploy
openenv push --repo-id ravi/sql-query-reviewer

# Verify
curl -s -o /dev/null -w "%{http_code}" -X POST https://ravi-sql-query-reviewer.hf.space/reset -H "Content-Type: application/json" -d '{}'
# Expected: 200
```

## Environment Variables for Inference

```bash
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
export HF_TOKEN="hf_xxxxxxxxxxxxx"
export IMAGE_NAME="sql-query-reviewer"
```

## Pre-Validation

```bash
chmod +x validate-submission.sh
./validate-submission.sh https://ravi-sql-query-reviewer.hf.space .
```

Expected output: All 3/3 checks passed.
