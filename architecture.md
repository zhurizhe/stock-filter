# architecture.md

## Purpose
- provide a lightweight workspace for Tushare Pro data pulls that can later support stock-filter logic

## Layout
- `scripts/`: shared helper plus endpoint-specific CLI scripts
- `TASKS/`: active and backlog task tracking
- `MEMORY/`: durable decisions, risks, bugs, metrics, and notes
- `SESSIONS/`: timestamped change logs

## Data Flow
1. script loads `.env`
2. helper resolves `TUSHARE_TOKEN`
3. helper creates a `tushare.pro_api()` client
4. endpoint script issues one API call
5. result prints to stdout or writes to CSV
