# 12 — Testing Strategy

## Level 1: Unit Tests (During Build)
- **Models:** Validate Pydantic models accept/reject correct/incorrect data
- **Grader:** Test with known inputs → known scores. Verify determinism (run 10x, same result).
- **Reward function:** Test each action type returns expected reward range
- **Fuzzy matcher:** Test with exact match, partial match, no match, already-found cases

## Level 2: Integration Tests (Before Docker)
- Run `uv run server` locally
- POST `/reset` with each task ID → verify valid observation returned
- POST `/step` with valid action → verify reward, done, observation
- POST `/step` with invalid action → verify graceful error handling
- GET `/state` → verify state matches expectations
- Run full episode: reset → steps → done → verify final grader score

## Level 3: Container Tests (Before Deploy)
```bash
docker build -t sql-query-reviewer ./server
docker run -d -p 8000:8000 sql-query-reviewer
# Wait for startup
sleep 5
# Test reset
curl -X POST http://localhost:8000/reset -d '{}' | python -m json.tool
# Test step
curl -X POST http://localhost:8000/step -d '{"action_type":"identify_issue","issue_category":"syntax","issue_description":"test"}' | python -m json.tool
docker stop $(docker ps -q)
```

## Level 4: Validation Tests (Before Submit)
- `openenv validate` — must pass
- `validate-submission.sh <url> .` — all 3 checks must pass
- Run `inference.py` 3 times → verify scores are consistent
- Verify stdout format matches `[START]`, `[STEP]`, `[END]` exactly
- Check memory usage stays under 8GB
- Check runtime stays under 20 minutes

## Level 5: Score Variance Check
- Run inference on all 3 tasks → verify different scores
- Confirm no grader returns the same score for different inputs
- Verify easy > medium > hard in terms of baseline agent performance

## DQ Prevention Checklist
- [ ] HF Space returns 200 on POST /reset
- [ ] openenv.yaml is valid
- [ ] Typed models work
- [ ] Dockerfile builds
- [ ] 3+ tasks with graders returning 0.0-1.0
- [ ] Graders DON'T always return the same score
- [ ] inference.py exists in root
- [ ] Baseline produces reproducible scores
- [ ] Not plagiarized from existing environments
