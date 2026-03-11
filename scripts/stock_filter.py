from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pandas as pd


AMOUNT_UNIT_YUAN = 1000
PASS_GRADE = "pass"
DEGRADED_GRADE = "degraded"
EXCLUDED_GRADE = "excluded"
WAITING_GRADE = "waiting"


def _to_trade_date(value: object) -> pd.Timestamp | None:
    if value is None or value == "":
        return None
    return pd.to_datetime(str(value))


def _normalize_trade_dates(values: Iterable[object] | None) -> set[str]:
    if not values:
        return set()
    normalized: set[str] = set()
    for value in values:
        trade_date = _to_trade_date(value)
        if trade_date is not None:
            normalized.add(trade_date.strftime("%Y%m%d"))
    return normalized


def _prepare_price_frame(
    daily_df: pd.DataFrame,
    *,
    required_columns: set[str],
    numeric_columns: list[str],
) -> pd.DataFrame:
    missing_columns = sorted(required_columns - set(daily_df.columns))
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

    frame = daily_df.copy()
    frame["trade_date"] = pd.to_datetime(frame["trade_date"].astype(str))
    frame[numeric_columns] = frame[numeric_columns].apply(pd.to_numeric, errors="coerce")
    frame = frame.sort_values("trade_date").drop_duplicates("trade_date", keep="last")
    frame = frame.dropna(subset=numeric_columns).reset_index(drop=True)
    return frame


def _grade_pullback_duration(pullback_days: int) -> str:
    if 3 <= pullback_days <= 8:
        return PASS_GRADE
    if 9 <= pullback_days <= 10:
        return DEGRADED_GRADE
    if pullback_days > 10:
        return EXCLUDED_GRADE
    return WAITING_GRADE


def _grade_pullback_depth(pullback_ratio: float) -> str:
    if pullback_ratio <= 0.5:
        return PASS_GRADE
    if pullback_ratio <= 0.618:
        return DEGRADED_GRADE
    return EXCLUDED_GRADE


def _pullback_score(grade: str) -> int:
    if grade == PASS_GRADE:
        return 2
    if grade == DEGRADED_GRADE:
        return 1
    return 0


def _downgrade_grade(grade: str) -> str:
    if grade == PASS_GRADE:
        return DEGRADED_GRADE
    if grade == DEGRADED_GRADE:
        return EXCLUDED_GRADE
    return grade


def _grade_volume_contraction(pullback_vol_mean: float, vol20: float) -> str:
    if vol20 <= 0:
        return EXCLUDED_GRADE
    contraction_ratio = pullback_vol_mean / vol20
    if contraction_ratio <= 0.7:
        return PASS_GRADE
    if contraction_ratio <= 0.9:
        return DEGRADED_GRADE
    return EXCLUDED_GRADE


def _build_pullback_context(
    daily_df: pd.DataFrame,
    *,
    recent_window: int,
    breakout_volume_ratio: float,
    required_columns: set[str] | None = None,
    numeric_columns: list[str] | None = None,
) -> dict[str, Any]:
    required = {"trade_date", "close", "high", "low", "vol"}
    if required_columns:
        required |= required_columns
    numeric = ["close", "high", "low", "vol"]
    if numeric_columns:
        numeric.extend(numeric_columns)
    frame = _prepare_price_frame(
        daily_df,
        required_columns=required,
        numeric_columns=list(dict.fromkeys(numeric)),
    )

    if len(frame) < recent_window:
        return {
            "ok": False,
            "error": f"Need at least {recent_window} trading days.",
            "checks": {"enough_history": False},
        }

    frame["ma20_series"] = frame["close"].rolling(20, min_periods=20).mean()
    frame["vol20_series"] = frame["vol"].rolling(20, min_periods=20).mean()
    frame["pct_change"] = frame["close"].pct_change()

    recent = frame.tail(recent_window).copy().reset_index(drop=True)
    recent["prior_high"] = recent["high"].cummax().shift(1)
    vol20 = float(recent["vol"].mean())
    breakout_mask = (
        recent["prior_high"].notna()
        & (recent["high"] > recent["prior_high"])
        & (recent["vol"] >= breakout_volume_ratio * vol20)
    )

    if not breakout_mask.any():
        return {
            "ok": False,
            "error": "No recent volume breakout found.",
            "checks": {
                "enough_history": True,
                "has_breakout": False,
            },
        }

    breakout_pos = int(recent.index[breakout_mask][-1])
    breakout_row = recent.loc[breakout_pos]
    breakout_trade_date = breakout_row["trade_date"]
    breakout_low = float(breakout_row["low"])

    swing_window = recent.loc[breakout_pos:].copy()
    swing_high_pos = int(swing_window["high"].idxmax())
    swing_high_row = recent.loc[swing_high_pos]
    swing_high_trade_date = swing_high_row["trade_date"]
    swing_high = float(swing_high_row["high"])

    if swing_high <= breakout_low:
        return {
            "ok": False,
            "error": "Invalid breakout range.",
            "checks": {
                "enough_history": True,
                "has_breakout": True,
            },
        }

    pullback_frame = frame[frame["trade_date"] > swing_high_trade_date].copy().reset_index(drop=True)
    pullback_days = int(len(pullback_frame))
    pullback_low = swing_high if pullback_frame.empty else float(pullback_frame["low"].min())
    pullback_ratio = float((swing_high - pullback_low) / (swing_high - breakout_low))

    return {
        "ok": True,
        "frame": frame,
        "recent": recent,
        "trade_date": recent.iloc[-1]["trade_date"].strftime("%Y%m%d"),
        "breakout_trade_date": breakout_trade_date.strftime("%Y%m%d"),
        "swing_high_trade_date": swing_high_trade_date.strftime("%Y%m%d"),
        "breakout_low": breakout_low,
        "swing_high": swing_high,
        "pullback_low": pullback_low,
        "pullback_days": pullback_days,
        "pullback_ratio": pullback_ratio,
        "pullback_frame": pullback_frame,
        "vol20": vol20,
    }


def evaluate_strong_background(
    daily_df: pd.DataFrame,
    *,
    stock_name: str = "",
    list_date: object | None = None,
    negative_announcement_dates: Iterable[object] | None = None,
    min_listing_days: int = 60,
    min_runup_pct_20: float = 0.20,
    volume_spike_ratio: float = 1.5,
    min_avg_amount_yuan: float = 300_000_000,
) -> dict[str, Any]:
    numeric_columns = ["close", "high", "vol", "amount"]
    if "low" in daily_df.columns:
        numeric_columns.append("low")
    frame = _prepare_price_frame(
        daily_df,
        required_columns={"trade_date", "close", "high", "vol", "amount"},
        numeric_columns=numeric_columns,
    )

    if len(frame) < 20:
        return {
            "passed": False,
            "score": 0,
            "error": "Need at least 20 trading days.",
            "checks": {"enough_history": False},
        }

    recent20 = frame.tail(20).copy()
    recent10 = frame.tail(10).copy()
    price_floor = recent20["low"].cummin() if "low" in recent20.columns else recent20["close"].cummin()
    max_runup_pct_20 = float((recent20["high"] / price_floor - 1).max())
    vol20 = float(recent20["vol"].mean())
    max_vol_ratio_20 = float((recent20["vol"] / vol20).max()) if vol20 > 0 else 0.0
    current_close = float(recent20["close"].iloc[-1])
    ma10 = float(recent10["close"].mean())
    ma20 = float(recent20["close"].mean())
    avg_amount_yuan_20 = float(recent20["amount"].mean() * AMOUNT_UNIT_YUAN)

    current_trade_date = recent20["trade_date"].iloc[-1]
    current_trade_date_str = current_trade_date.strftime("%Y%m%d")
    normalized_name = stock_name.upper()
    is_st = "ST" in normalized_name

    listed_at = _to_trade_date(list_date)
    days_since_listed = None
    is_new_stock = False
    if listed_at is not None:
        days_since_listed = int((current_trade_date.normalize() - listed_at.normalize()).days)
        is_new_stock = days_since_listed < min_listing_days

    negative_dates = _normalize_trade_dates(negative_announcement_dates)
    is_negative_announcement_day = current_trade_date_str in negative_dates

    checks = {
        "enough_history": True,
        "max_runup_pct_20": max_runup_pct_20 >= min_runup_pct_20,
        "volume_spike": max_vol_ratio_20 >= volume_spike_ratio,
        "close_ge_ma20": current_close >= ma20,
        "ma10_ge_ma20": ma10 >= ma20,
        "avg_amount_ge_threshold": avg_amount_yuan_20 >= min_avg_amount_yuan,
        "not_st": not is_st,
        "not_new_stock": not is_new_stock,
        "not_negative_announcement_day": not is_negative_announcement_day,
    }

    return {
        "passed": all(checks.values()),
        "score": 2 if all(checks.values()) else 0,
        "trade_date": current_trade_date_str,
        "days_since_listed": days_since_listed,
        "max_runup_pct_20": max_runup_pct_20,
        "vol20": vol20,
        "max_vol_ratio_20": max_vol_ratio_20,
        "close": current_close,
        "ma10": ma10,
        "ma20": ma20,
        "avg_amount_yuan_20": avg_amount_yuan_20,
        "checks": checks,
    }


def evaluate_pullback_quality(
    daily_df: pd.DataFrame,
    *,
    recent_window: int = 20,
    breakout_volume_ratio: float = 1.5,
) -> dict[str, Any]:
    context = _build_pullback_context(
        daily_df,
        recent_window=recent_window,
        breakout_volume_ratio=breakout_volume_ratio,
    )

    if not context["ok"]:
        return {
            "passed": False,
            "grade": EXCLUDED_GRADE,
            "score": 0,
            "error": context["error"],
            "checks": context["checks"],
        }

    frame = context["frame"]
    pullback_days = int(context["pullback_days"])
    pullback_ratio = float(context["pullback_ratio"])
    duration_grade = _grade_pullback_duration(pullback_days)
    depth_grade = _grade_pullback_depth(pullback_ratio)

    pullback_frame = context["pullback_frame"].copy()
    below_ma20 = (pullback_frame["close"] < pullback_frame["ma20_series"]).fillna(False)
    consecutive_below_ma20 = bool((below_ma20 & below_ma20.shift(1, fill_value=False)).any())
    sharp_break_mask = (
        (pullback_frame["pct_change"] < -0.05)
        & (pullback_frame["close"] < pullback_frame["ma20_series"])
        & (pullback_frame["vol"] >= 1.2 * pullback_frame["vol20_series"])
    )
    ma20_broken = bool(consecutive_below_ma20 or sharp_break_mask.fillna(False).any())

    if ma20_broken or duration_grade == EXCLUDED_GRADE or depth_grade == EXCLUDED_GRADE:
        grade = EXCLUDED_GRADE
    elif duration_grade == PASS_GRADE and depth_grade == PASS_GRADE:
        grade = PASS_GRADE
    elif duration_grade == WAITING_GRADE:
        grade = WAITING_GRADE
    else:
        grade = DEGRADED_GRADE

    checks = {
        "enough_history": True,
        "has_breakout": True,
        "duration_ok": duration_grade == PASS_GRADE,
        "duration_degraded": duration_grade == DEGRADED_GRADE,
        "depth_ok": depth_grade == PASS_GRADE,
        "depth_degraded": depth_grade == DEGRADED_GRADE,
        "ma20_intact": not ma20_broken,
    }

    return {
        "passed": grade == PASS_GRADE,
        "grade": grade,
        "score": _pullback_score(grade),
        "trade_date": context["trade_date"],
        "breakout_trade_date": context["breakout_trade_date"],
        "swing_high_trade_date": context["swing_high_trade_date"],
        "breakout_low": context["breakout_low"],
        "swing_high": context["swing_high"],
        "pullback_low": context["pullback_low"],
        "pullback_days": pullback_days,
        "pullback_ratio": pullback_ratio,
        "ma20_broken": ma20_broken,
        "checks": checks,
    }


def evaluate_volume_contraction_quality(
    daily_df: pd.DataFrame,
    *,
    recent_window: int = 20,
    breakout_volume_ratio: float = 1.5,
    min_turnover_rate: float = 1.0,
    min_avg_amount_yuan: float = 500_000_000,
) -> dict[str, Any]:
    context = _build_pullback_context(
        daily_df,
        recent_window=recent_window,
        breakout_volume_ratio=breakout_volume_ratio,
        required_columns={"amount", "turnover_rate"},
        numeric_columns=["amount", "turnover_rate"],
    )

    if not context["ok"]:
        return {
            "passed": False,
            "grade": EXCLUDED_GRADE,
            "score": 0,
            "error": context["error"],
            "checks": context["checks"],
        }

    pullback_frame = context["pullback_frame"].copy()
    if pullback_frame.empty:
        return {
            "passed": False,
            "grade": WAITING_GRADE,
            "score": 0,
            "error": "Pullback not started.",
            "checks": {
                "enough_history": True,
                "has_breakout": True,
                "has_pullback": False,
            },
        }

    vol20 = float(context["vol20"])
    pullback_vol_mean = float(pullback_frame["vol"].mean())
    pullback_vol_ratio = pullback_vol_mean / vol20 if vol20 > 0 else 0.0
    raw_grade = _grade_volume_contraction(pullback_vol_mean, vol20)
    pullback_turnover_rate_mean = float(pullback_frame["turnover_rate"].mean())
    pullback_avg_amount_yuan = float(pullback_frame["amount"].mean() * AMOUNT_UNIT_YUAN)
    liquidity_warning = (
        pullback_turnover_rate_mean < min_turnover_rate
        and pullback_avg_amount_yuan < min_avg_amount_yuan
    )
    grade = _downgrade_grade(raw_grade) if liquidity_warning else raw_grade

    checks = {
        "enough_history": True,
        "has_breakout": True,
        "has_pullback": True,
        "volume_contraction_strong": raw_grade == PASS_GRADE,
        "volume_contraction_acceptable": raw_grade in {PASS_GRADE, DEGRADED_GRADE},
        "liquidity_ok": not liquidity_warning,
    }

    return {
        "passed": grade == PASS_GRADE,
        "grade": grade,
        "score": _pullback_score(grade),
        "trade_date": context["trade_date"],
        "breakout_trade_date": context["breakout_trade_date"],
        "swing_high_trade_date": context["swing_high_trade_date"],
        "pullback_days": context["pullback_days"],
        "pullback_vol_mean": pullback_vol_mean,
        "pullback_vol_ratio": pullback_vol_ratio,
        "pullback_turnover_rate_mean": pullback_turnover_rate_mean,
        "pullback_avg_amount_yuan": pullback_avg_amount_yuan,
        "vol20": vol20,
        "raw_grade": raw_grade,
        "liquidity_warning": liquidity_warning,
        "checks": checks,
    }


def evaluate_stock_filter(daily_df: pd.DataFrame, **kwargs: Any) -> dict[str, Any]:
    return evaluate_strong_background(daily_df, **kwargs)


def passes_stock_filter(**kwargs: Any) -> bool:
    return bool(evaluate_stock_filter(**kwargs)["passed"])


def passes_strong_background(**kwargs: Any) -> bool:
    return bool(evaluate_strong_background(**kwargs)["passed"])
