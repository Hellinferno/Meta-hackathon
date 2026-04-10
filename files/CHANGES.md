# Changes to Apply — Priority Order

## 🚨 CRITICAL FIX (Do this first — DQ risk)

### 1. Replace `inference.py`
**File:** `inference.py` (root directory)
**Problem:** Current stdout format outputs JSON like `[START] {"difficulty": "easy", ...}` instead of the required `[START] task=easy_001 env=sql-query-reviewer model=Qwen/...` format.
**Impact:** The hackathon dashboard explicitly states: "Any deviation in field names, ordering, or formatting will result in incorrect evaluation scoring."
**Fix:** Replace with the provided `inference.py` that uses `log_start()`, `log_step()`, `log_end()` matching the exact spec format.

**Key changes in the new inference.py:**
- `[START] task=<task_name> env=<benchmark> model=<model_name>` — flat key=value, not JSON
- `[STEP] step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>` — reward formatted to 2 decimal places
- `[END] success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>` — comma-separated rewards list
- Uses `API_BASE_URL` defaulting to HF router (not openai.com)
- Uses `HF_TOKEN` as primary API key env var
- Accumulates rewards list and computes success boolean
- try/finally ensures [END] is always emitted even on exception

---

## ⚠️ HIGH PRIORITY

### 2. Replace `openenv.yaml`
**Problem:** Task IDs in yaml (`easy_syntax`, `medium_performance`, `hard_security`) don't match actual task IDs in JSON files (`easy_001`–`easy_005`, `medium_001`–`medium_005`, `hard_001`–`hard_005`).
**Impact:** If `openenv validate` checks task ID alignment, validation fails.
**Fix:** Replace with provided `openenv.yaml` listing all 15 actual task IDs.

### 3. Replace `Dockerfile`
**Problem:** No HEALTHCHECK instruction and no `curl` installed.
**Fix:** Added `apt-get install curl` and `HEALTHCHECK` directive.

### 4. Replace `README.md`
**Problem:** Functional but not compelling for human reviewers (30% weight on real-world utility).
**Fix:** Added "Why This Matters" narrative, baseline score table, cleaner structure.

---

## 🟡 MEDIUM PRIORITY (before deadline if time permits)

### 5. Merge PR #1 on GitHub
The fix/package-server-and-inference-imports branch is already deployed to HF Spaces but still a draft PR on GitHub. Merge it so `main` branch CI passes.

### 6. Verify `openenv` tag on HF Space
Go to Space settings on HuggingFace and confirm the `openenv` tag is applied. The README has it in YAML front matter tags, but double-check it appears in the Space metadata.

### 7. Run pre-validation
```bash
./validate-submission.sh https://hellinferno-sql-query-reviewer.hf.space .
```

---

## How to apply these changes

```bash
# From your local repo directory:
cp /path/to/fixes/inference.py ./inference.py
cp /path/to/fixes/openenv.yaml ./openenv.yaml
cp /path/to/fixes/Dockerfile ./Dockerfile
cp /path/to/fixes/README.md ./README.md

# Test locally
uvicorn server.app:app --port 8000 &
python inference.py  # verify [START]/[STEP]/[END] format

# Push to HF Spaces
git add -A
git commit -m "fix: correct inference stdout format and align openenv.yaml task IDs"
git push origin main
git push hf main
```
