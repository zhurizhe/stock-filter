# decisions.md

## 2026-03-11

### Change Class
- E

### Decision
- bootstrap a full memory topology and keep Tushare integration as small CLI scripts with one shared helper

### Why
- the repository started empty, so continuity and a deterministic working loop needed to exist before feature work
- a shared helper keeps token handling and output behavior consistent without introducing a larger package structure

### Rollback
- remove memory files, `requirements.txt`, `.env.example`, and the `scripts/` files introduced in this session

### Impact
- future sessions can resume from repository state alone
- Tushare calls can be extended without repeating auth and output code

### Follow-up
- add higher-level stock screening scripts after token-backed smoke tests are available

## 2026-03-11

### Change Class
- C

### Decision
- add a pure stock-filter function that evaluates a single symbol from `daily`行情和外部元数据，不在函数内部抓公告

### Why
- “重大负面公告日”依赖外部公告口径，直接写死数据源会让筛选规则和数据接入耦合
- 纯函数更容易复用到批量筛选、回测和单票调试

### Rollback
- remove `scripts/stock_filter.py` and revert this decision entry

### Impact
- rule evaluation is now reusable with any upstream data source
- future CLI can focus on data fetching and orchestration

### Follow-up
- add a CLI or batch runner that fetches market data and passes announcement-date inputs

## 2026-03-11

### Change Class
- C

### Decision
- add a live batch screener that fetches recent trade dates, market-wide `daily`, and `stock_basic`, then automatically trims to the latest complete 20-day window

### Why
- evaluating one symbol at a time is not enough to verify the rule set against the real universe
- intraday runs can include today in `trade_cal` before full `daily` rows are available, which would otherwise make every symbol fail on history length

### Rollback
- remove `scripts/run_stock_filter.py`, `tests/test_stock_filter.py`, and revert this decision entry

### Impact
- the repository can now run the screen end-to-end with a single command
- live runs are stable during market hours because incomplete trade dates are filtered out

### Follow-up
- attach a real negative-announcement feed and decide whether to persist CSV outputs by default

## 2026-03-11

### Change Class
- C

### Decision
- split the old filter into `strong background` and `pullback quality`, and score them as `2 + 2` with the live screener defaulting to `4` points only

### Why
- the user wants the original momentum filter to represent background strength, while pullback quality is a separate layer with downgrade / exclusion states
- keeping the downgrade as `1` point preserves ranking information without polluting the default `4`-point output

### Rollback
- remove `evaluate_pullback_quality()`, revert `run_stock_filter.py` to the prior strong-background-only mode, and revert this decision entry

### Impact
- the screener now exposes both strict `4`-point names and softer `3`-point near-misses
- live runs are more selective and easier to interpret by setup quality

### Follow-up
- decide whether `3`-point names should be exported as a separate watchlist by default

## 2026-03-11

### Change Class
- C

### Decision
- add a separate `volume contraction quality` scorer, reuse the same breakout/pullback context as pullback-quality, and change the live screener to score `2 + 2 + 2` while defaulting to `>=5`

### Why
- the user wants缩量质量单独记 2 分，并要求用回踩阶段平均量对比 `vol20`
- “假缩量”需要结合 `turnover_rate` 和回踩阶段日均成交额判断，批量脚本必须补拉 `daily_basic`
- shared context keeps breakout / swing-high / pullback detection consistent across the two pullback-related scorers

### Rollback
- remove `evaluate_volume_contraction_quality()`, inline the old pullback-only context in `scripts/stock_filter.py`, revert `scripts/run_stock_filter.py` to `2 + 2`, and revert this decision entry

### Impact
- live screening now distinguishes真实缩量、可接受缩量、以及弱缩量/流动性衰减
- default output can retain one degraded dimension by keeping `>=5` instead of forcing a perfect `6`

### Follow-up
- decide whether `raw_grade` and downgraded grade should both be exported in CSV by default
