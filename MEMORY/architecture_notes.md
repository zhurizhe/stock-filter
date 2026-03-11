# architecture_notes.md

## Bootstrap Notes
- repository is intentionally minimal: memory documents plus standalone Python scripts
- `scripts/tushare_common.py` owns env loading, token resolution, client construction, and output writing
- endpoint scripts stay single-purpose and forward CLI args directly to Tushare Pro methods
- `scripts/stock_filter.py` keeps筛选规则纯粹，只消费行情和外部传入的公告/上市信息
- `scripts/run_stock_filter.py` orchestrates `trade_cal` + market-wide `daily` + `stock_basic`, then evaluates the last complete 20-day window
- `scripts/stock_filter.py` now exposes two layers: strong background (`2`) and pullback quality (`2` / `1` / `0`)
