# CONTINUITY.md

## SYSTEM STATE
Current objective:
- add volume-contraction-quality scoring on top of the strong-background and pullback filters

Current module:
- scoring / batch screener

Current phase:
- live scoring completed

Last updated:
- 2026-03-11

## ACTIVE TASK
- task: add volume-contraction-quality scoring and rerun the screener
- status: done
- owner: agent

## COMPLETED RECENTLY
- added `evaluate_pullback_quality()` and explicit `evaluate_strong_background()`
- added shared pullback-context detection plus `evaluate_volume_contraction_quality()`
- updated the screener to score `2 + 2 + 2`, merge `daily_basic.turnover_rate`, and keep default `>=5`-point stocks
- passed 9 unit tests in `.venv`
- live run on 2026-03-11 completed and returned no rows under the new default threshold

## NEXT ACTIONS
- [ ] define the upstream source for “重大负面公告日”
- [ ] decide whether `4`-point degraded names should be exported as watchlist candidates
- [ ] optionally save/export live runs to CSV snapshots
- [ ] decide whether “新股” should use calendar days, trading days, or a larger threshold

## BLOCKERS
- none

## RISKS
1. live results currently do not exclude “重大负面公告日” unless a CSV source is supplied
2. missing `daily_basic.turnover_rate` rows will suppress volume-contraction scoring for affected symbols
3. the new 5-point filter is strict enough that a given day may legitimately return 0 stocks
