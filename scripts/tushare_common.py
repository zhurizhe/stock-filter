from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
TOKEN_KEYS = ("TUSHARE_TOKEN", "TUSHARE_PRO_TOKEN", "TS_TOKEN")


def load_env_file(path: Path = ENV_PATH) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        os.environ.setdefault(key, value)


def resolve_token() -> str:
    load_env_file()
    for key in TOKEN_KEYS:
        token = os.getenv(key)
        if token:
            return token
    keys = ", ".join(TOKEN_KEYS)
    raise SystemExit(f"Missing Tushare token. Set one of: {keys}")


def get_pro_client():
    import tushare as ts

    token = resolve_token()
    ts.set_token(token)
    return ts.pro_api(token)


def emit_dataframe(df, output: str | None, limit: int) -> None:
    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        print(output_path)
        return
    if df.empty:
        print("No rows returned.")
        return
    print(df.head(limit).to_csv(index=False).strip())
