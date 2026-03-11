## Active Objective
- add volume-contraction-quality scoring and rerun the live screener

## Current Status
- phase: complete
- owner: agent

## In Progress
- [x] add `evaluate_volume_contraction_quality()` with downgrade-on-liquidity behavior
- [x] reuse a shared pullback-context detector across pullback and volume scoring
- [x] update `scripts/run_stock_filter.py` to score `2 + 2 + 2` and keep default `>=5`-point stocks
- [x] rerun tests and a live screen with the new scoring

## DoD For This Task
- [x] volume-contraction-quality function returns deterministic grading and score
- [x] 9 unit tests pass in `.venv`
- [x] one real run completes with the new `>=5` score threshold
- [x] validation results are written back to memory files
