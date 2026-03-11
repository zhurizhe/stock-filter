# known_issues.md

## Current
- live Tushare requests require `TUSHARE_TOKEN` in `.env` or process environment
- dependencies are declared but not installed by this task
- Homebrew-managed Python blocks global `pip install`; prefer `.venv` for local execution
- batch runs do not exclude “重大负面公告日” unless `--negative-announcements` is provided
- the default `4`-point filter may legitimately return no names on some dates
