# CONTINUITY.md

## SYSTEM STATE
Current objective:
- add pullback-quality scoring on top of the strong-background filter

Current module:
- scoring / batch screener

Current phase:
- live scoring completed

Last updated:
- 2026-03-11

## ACTIVE TASK
- task: add pullback-quality scoring and rerun the screener
- status: done
- owner: agent

## COMPLETED RECENTLY
- added `evaluate_pullback_quality()` and explicit `evaluate_strong_background()`
- updated the screener to score `2 + 2` and keep only default `4`-point stocks
- passed 6 unit tests in `.venv`
- live run on 2026-03-11 returned 0 four-point stocks and 7 three-point near-misses using data through 20260310

## NEXT ACTIONS
- [ ] define the upstream source for “重大负面公告日”
- [ ] decide whether degraded pullbacks should be kept as watchlist candidates
- [ ] optionally save/export live runs to CSV snapshots
- [ ] decide whether “新股” should use calendar days, trading days, or a larger threshold

## BLOCKERS
- none

## RISKS
1. live results currently do not exclude “重大负面公告日” unless a CSV source is supplied
2. the new 4-point filter is strict enough that a given day may legitimately return 0 stocks
