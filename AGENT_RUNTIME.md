# AGENT_RUNTIME.md

Runtime protocol for `stock-filter`.

## Non-Negotiables
- confirm repository state before edits
- avoid silent structural drift
- validate before claiming completion
- persist memory updates on every finished task

## Boot Sequence
1. Read `AGENTS.md`
2. Read `AGENT_RUNTIME.md`
3. Read `CONTINUITY.md`
4. Read `architecture.md`
5. Read `TASKS/active.md`
6. Read `MEMORY/decisions.md`
7. Summarize phase, objective, blockers, and next actions

## Working Loop
1. Plan the smallest viable change
2. Edit only the files needed
3. Run at least one concrete validation step
4. Persist continuity, task, and memory updates
