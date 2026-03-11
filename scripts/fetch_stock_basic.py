from __future__ import annotations

import argparse

from tushare_common import emit_dataframe, get_pro_client


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch stock_basic from Tushare Pro.")
    parser.add_argument("--list-status", default="L", help="L, D, or P")
    parser.add_argument("--exchange", default="", help="SSE, SZSE, or BSE")
    parser.add_argument("--market", default="", help="Main, ChiNext, STAR, or others")
    parser.add_argument(
        "--fields",
        default="ts_code,symbol,name,area,industry,market,list_date",
        help="Comma-separated Tushare fields.",
    )
    parser.add_argument("--limit", type=int, default=20, help="Rows to print when not saving.")
    parser.add_argument("--output", help="Optional CSV output path.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    pro = get_pro_client()
    df = pro.stock_basic(
        exchange=args.exchange,
        list_status=args.list_status,
        market=args.market,
        fields=args.fields,
    )
    emit_dataframe(df, args.output, args.limit)


if __name__ == "__main__":
    main()
