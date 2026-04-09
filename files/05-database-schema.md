# 05 — Task Bank Schema

## Overview
Tasks are stored as JSON files, not a database. Each difficulty level has its own file with 3-5 queries.

## Easy Tasks (`tasks/easy_tasks.json`)

Queries with obvious syntax errors, wrong keywords, basic logic mistakes. An LLM should score 0.7-0.9.

Example queries:
1. Misspelled keywords (SELCT, FORM, WEHRE)
2. Missing FROM clause
3. Wrong column names that don't exist in schema
4. Missing semicolons / unclosed quotes
5. Using = NULL instead of IS NULL

## Medium Tasks (`tasks/medium_tasks.json`)

Queries with performance anti-patterns. Requires understanding schema context. Target score: 0.4-0.6.

Example queries:
1. SELECT * on a 50-column table when only 2 columns needed
2. Missing index hint on a JOIN with large table
3. Correlated subquery that could be a JOIN
4. Missing LIMIT on unbounded query
5. Redundant DISTINCT on a column with UNIQUE constraint

## Hard Tasks (`tasks/hard_tasks.json`)

Security vulnerabilities + complex optimization. Target score: 0.2-0.4.

Example queries:
1. String concatenation enabling SQL injection
2. Privilege escalation via UNION with system tables
3. Data leakage through unfiltered JOIN exposing PII
4. Query that could use window functions instead of self-join (10x perf gain)
5. Missing transaction isolation causing phantom reads

## Ground Truth Format

Each issue in ground truth:
```json
{
  "category": "security",
  "description": "String concatenation in WHERE clause enables SQL injection",
  "severity": 1.0,
  "fix": "Use parameterized query with ? placeholder",
  "keywords": ["injection", "concatenation", "user input", "unsanitized"]
}
```

The `keywords` field is used by the grader for fuzzy matching against agent responses.
