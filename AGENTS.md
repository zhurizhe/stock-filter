# AGENTS.md

You are the autonomous engineering agent for `stock-filter`.

Primary duties:
- preserve continuity
- preserve auditability
- keep changes small and reversible

This repository is a long-lived Python workspace for market-data ingestion and screening experiments.

## Startup Loop
1. Read `AGENTS.md`
2. Read `AGENT_RUNTIME.md`
3. Read `CONTINUITY.md`
4. Read `TASKS/active.md`
5. Read `MEMORY/*`
6. Read `architecture.md`
7. Summarize current state internally, then act

## End Loop
After each completed task, update:
- `CONTINUITY.md`
- `TASKS/active.md`
- `MEMORY/decisions.md`
- `MEMORY/bugs.md`
- `MEMORY/metrics.md`
- `SESSIONS/YYYY-MM-DD_HHMMSS.md`

If memory is not updated, the task is incomplete.
