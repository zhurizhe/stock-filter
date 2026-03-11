## Active Objective
- add pullback-quality scoring and rerun the live screener

## Current Status
- phase: complete
- owner: agent

## In Progress
- [x] add `evaluate_pullback_quality()` with pass / degraded / excluded states
- [x] map strong background to 2 points and pullback quality to 2 points
- [x] update `scripts/run_stock_filter.py` to keep default `4`-point stocks
- [x] rerun tests and a live screen with the new scoring

## DoD For This Task
- [x] pullback-quality function returns deterministic grading and score
- [x] 6 unit tests pass in `.venv`
- [x] one real run completes with the new score threshold
- [x] validation results are written back to memory files
