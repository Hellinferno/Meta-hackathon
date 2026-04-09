# 01 — Problem Statement & Domain Selection

## Domain: SQL Query Review Environment

### The Real-World Problem
Every software team reviews SQL queries — in code reviews, database migrations, ETL pipeline audits, and security assessments. This is a genuine, high-frequency task that requires:
- Pattern recognition (anti-patterns, vulnerabilities)
- Domain knowledge (schema relationships, indexing strategies)
- Multi-step reasoning (understanding query intent before evaluating correctness)

### Why This Domain Wins

| Evaluation Criteria | Weight | How We Score |
|---|---|---|
| Real-world utility | 30% | SQL review is universal — Meta runs millions of queries daily. Fills a real gap in agent evaluation. |
| Task & grader quality | 25% | Clear ground truth per query, deterministic grading, natural difficulty progression |
| Environment design | 20% | Clean state (per-query episode), rich observations, well-typed actions, per-step rewards |
| Code quality & spec compliance | 15% | Full OpenEnv spec, clean project structure, Docker, typed models |
| Creativity & novelty | 10% | No SQL review env exists in OpenEnv. Reward design uses severity-weighted partial credit. |

### What the Agent Does
1. Receives a SQL query + optional schema context
2. Reviews it step-by-step, identifying issues (syntax, performance, security, logic)
3. Suggests fixes for each identified issue
4. Decides when to approve or flag the query
5. Gets rewarded for correctly identified issues and penalized for false positives

### Scope Boundaries
- **In scope**: SELECT, INSERT, UPDATE, DELETE queries; joins; subqueries; CTEs; window functions
- **Out of scope**: Stored procedures, database-specific dialect features, real database execution
- **Episode length**: 3-8 steps depending on query complexity
- **No external dependencies**: All query analysis is rule-based and deterministic
