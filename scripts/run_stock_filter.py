from __future__ import annotations

import argparse
from datetime import date

import pandas as pd

try:
    from .stock_filter import evaluate_pullback_quality, evaluate_strong_background
    from .tushare_common import emit_dataframe, get_pro_client
except ImportError:
    from stock_filter import evaluate_pullback_quality, evaluate_strong_background
    from tushare_common import emit_dataframe, get_pro_client


RESULT_COLUMNS = [
    "ts_code",
    "name",
    "trade_date",
    "strong_background_score",
    "pullback_quality_score",
    "total_score",
    "pullback_quality_grade",
    "pullback_days",
    "pullback_ratio",
    "breakout_trade_date",
    "swing_high_trade_date",
    "close",
    "ma10",
    "ma20",
    "max_runup_pct_20",
    "max_vol_ratio_20",
    "avg_amount_yuan_20",
    "days_since_listed",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the stock filter across the live universe.")
    parser.add_argument("--end-date", default=date.today().strftime("%Y%m%d"), help="YYYYMMDD")
    parser.add_argument("--window", type=int, default=20, help="Recent trading days to evaluate.")
    parser.add_argument("--limit", type=int, default=50, help="Rows to print when not saving.")
    parser.add_argument("--output", help="Optional CSV output path.")
    parser.add_argument("--min-score", type=int, default=4, help="Minimum total score to keep.")
    parser.add_argument(
        "--negative-announcements",
        help="Optional CSV with ts_code and trade_date columns.",
    )
    parser.add_argument("--min-listing-days", type=int, default=60, help="Minimum natural listing days.")
    return parser


def load_negative_announcement_map(path: str | None) -> dict[str, set[str]]:
    if not path:
        return {}
    frame = pd.read_csv(path, dtype=str)
    required_columns = {"ts_code", "trade_date"}
    missing_columns = sorted(required_columns - set(frame.columns))
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
    frame["trade_date"] = pd.to_datetime(frame["trade_date"].astype(str)).dt.strftime("%Y%m%d")
    return {
        ts_code: set(group["trade_date"])
        for ts_code, group in frame.groupby("ts_code", sort=False)
    }


def get_recent_trade_dates(pro, end_date: str, window: int, buffer_days: int = 10) -> list[str]:
    end_ts = pd.to_datetime(end_date)
    start_date = (end_ts - pd.Timedelta(days=max(window * 3, 60))).strftime("%Y%m%d")
    calendar = pro.trade_cal(
        start_date=start_date,
        end_date=end_ts.strftime("%Y%m%d"),
        is_open="1",
        fields="cal_date",
    )
    trade_dates = calendar.sort_values("cal_date").tail(window + buffer_days)["cal_date"].astype(str).tolist()
    if len(trade_dates) < window:
        raise SystemExit(f"Only found {len(trade_dates)} trade dates before {end_date}.")
    return trade_dates


def fetch_daily_window(pro, trade_dates: list[str]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for trade_date in trade_dates:
        frame = pro.daily(
            trade_date=trade_date,
            fields="ts_code,trade_date,open,high,low,close,vol,amount",
        )
        if not frame.empty:
            frames.append(frame)
    if not frames:
        raise SystemExit("No daily rows returned for the requested window.")
    return pd.concat(frames, ignore_index=True)


def screen_universe(
    pro,
    *,
    end_date: str,
    window: int,
    min_score: int = 4,
    negative_announcement_map: dict[str, set[str]] | None = None,
    min_listing_days: int = 60,
) -> pd.DataFrame:
    negative_announcement_map = negative_announcement_map or {}
    history_window = window + 19
    trade_dates = get_recent_trade_dates(pro, end_date=end_date, window=history_window)
    daily_df = fetch_daily_window(pro, trade_dates)
    available_trade_dates = sorted(daily_df["trade_date"].astype(str).unique().tolist())
    if len(available_trade_dates) < history_window:
        raise SystemExit(f"Only found {len(available_trade_dates)} available trade dates with daily data.")
    active_trade_dates = set(available_trade_dates[-history_window:])
    daily_df = daily_df[daily_df["trade_date"].astype(str).isin(active_trade_dates)].copy()
    stock_basic_df = pro.stock_basic(list_status="L", fields="ts_code,name,list_date")
    stock_basic_df = stock_basic_df.drop_duplicates("ts_code", keep="last").set_index("ts_code")

    results: list[dict[str, object]] = []
    for ts_code, group in daily_df.groupby("ts_code", sort=False):
        if ts_code not in stock_basic_df.index:
            continue
        stock_row = stock_basic_df.loc[ts_code]
        strong_result = evaluate_strong_background(
            group,
            stock_name=stock_row["name"],
            list_date=stock_row["list_date"],
            negative_announcement_dates=negative_announcement_map.get(ts_code, set()),
            min_listing_days=min_listing_days,
        )
        pullback_result = evaluate_pullback_quality(group, recent_window=window)
        strong_background_score = int(strong_result.get("score", 0))
        pullback_quality_score = int(pullback_result.get("score", 0))
        total_score = strong_background_score + pullback_quality_score
        if total_score < min_score:
            continue
        results.append(
            {
                "ts_code": ts_code,
                "name": stock_row["name"],
                "trade_date": strong_result["trade_date"],
                "strong_background_score": strong_background_score,
                "pullback_quality_score": pullback_quality_score,
                "total_score": total_score,
                "pullback_quality_grade": pullback_result["grade"],
                "pullback_days": pullback_result["pullback_days"],
                "pullback_ratio": pullback_result["pullback_ratio"],
                "breakout_trade_date": pullback_result["breakout_trade_date"],
                "swing_high_trade_date": pullback_result["swing_high_trade_date"],
                "close": strong_result["close"],
                "ma10": strong_result["ma10"],
                "ma20": strong_result["ma20"],
                "max_runup_pct_20": strong_result["max_runup_pct_20"],
                "max_vol_ratio_20": strong_result["max_vol_ratio_20"],
                "avg_amount_yuan_20": strong_result["avg_amount_yuan_20"],
                "days_since_listed": strong_result["days_since_listed"],
            }
        )

    if not results:
        return pd.DataFrame(columns=RESULT_COLUMNS)

    return pd.DataFrame(results).sort_values(
        ["total_score", "pullback_quality_score", "max_runup_pct_20", "max_vol_ratio_20", "avg_amount_yuan_20"],
        ascending=[False, False, False, False, False],
    )


def main() -> None:
    args = build_parser().parse_args()
    pro = get_pro_client()
    negative_announcement_map = load_negative_announcement_map(args.negative_announcements)
    result_df = screen_universe(
        pro,
        end_date=args.end_date,
        window=args.window,
        min_score=args.min_score,
        negative_announcement_map=negative_announcement_map,
        min_listing_days=args.min_listing_days,
    )
    emit_dataframe(result_df[RESULT_COLUMNS], args.output, args.limit)


if __name__ == "__main__":
    main()
