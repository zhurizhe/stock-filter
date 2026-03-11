from __future__ import annotations

import argparse

from tushare_common import emit_dataframe, get_pro_client


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch daily_basic from Tushare Pro.")
    parser.add_argument("--ts-code", help="Security code, for example 600000.SH")
    parser.add_argument("--trade-date", help="YYYYMMDD")
    parser.add_argument("--start-date", help="YYYYMMDD")
    parser.add_argument("--end-date", help="YYYYMMDD")
    parser.add_argument(
        "--fields",
        default="ts_code,trade_date,close,turnover_rate,volume_ratio,pe,pb,ps,total_mv,circ_mv",
        help="Comma-separated Tushare fields.",
    )
    parser.add_argument("--limit", type=int, default=20, help="Rows to print when not saving.")
    parser.add_argument("--output", help="Optional CSV output path.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if not any((args.ts_code, args.trade_date, args.start_date, args.end_date)):
        raise SystemExit("Provide --ts-code, --trade-date, or a date range.")
    pro = get_pro_client()
    df = pro.daily_basic(
        ts_code=args.ts_code,
        trade_date=args.trade_date,
        start_date=args.start_date,
        end_date=args.end_date,
        fields=args.fields,
    )
    emit_dataframe(df, args.output, args.limit)


if __name__ == "__main__":
    main()
