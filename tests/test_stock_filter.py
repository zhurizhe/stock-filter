from __future__ import annotations

import unittest

import pandas as pd

from scripts.stock_filter import (
    evaluate_pullback_quality,
    evaluate_stock_filter,
    evaluate_volume_contraction_quality,
)


def make_daily_frame() -> pd.DataFrame:
    rows = []
    for i in range(20):
        close = 10 + i * 0.2
        rows.append(
            {
                "trade_date": f"202501{(i + 2):02d}",
                "open": close - 0.1,
                "high": close * (1.03 if i == 19 else 1.01),
                "low": close * 0.99,
                "close": close,
                "vol": 1000 if i != 10 else 1800,
                "amount": 350000,
            }
        )
    return pd.DataFrame(rows)


def make_pullback_frame(
    *,
    final_lows: list[float],
    final_closes: list[float] | None = None,
    final_volumes: list[float] | None = None,
    final_amounts: list[float] | None = None,
    final_turnover_rates: list[float] | None = None,
) -> pd.DataFrame:
    dates = pd.bdate_range("2025-01-02", periods=40)
    rows = []

    for idx in range(20):
        close = 10.0 + 0.02 * (idx % 5)
        rows.append(
            {
                "trade_date": dates[idx].strftime("%Y%m%d"),
                "open": close,
                "high": close + 0.12,
                "low": close - 0.12,
                "close": close,
                "vol": 1000,
                "amount": 600000,
                "turnover_rate": 2.0,
            }
        )

    breakout_and_rise = [
        (10.20, 10.32, 10.10, 10.25, 1000),
        (10.18, 10.30, 10.08, 10.22, 1000),
        (10.15, 10.28, 10.05, 10.20, 1000),
        (10.22, 10.35, 10.10, 10.30, 1000),
        (10.40, 11.20, 10.30, 11.00, 2500),
        (11.05, 11.80, 10.90, 11.60, 1400),
        (11.65, 12.30, 11.40, 12.10, 1350),
        (12.05, 12.90, 11.90, 12.70, 1350),
        (12.80, 13.70, 12.60, 13.40, 1400),
        (13.35, 14.30, 13.10, 14.00, 1450),
        (14.05, 15.20, 13.80, 14.80, 1500),
        (14.70, 15.30, 14.50, 15.00, 1400),
        (14.95, 15.45, 14.80, 15.10, 1380),
        (15.05, 15.55, 14.90, 15.20, 1360),
        (15.20, 15.70, 15.00, 15.30, 1340),
    ]

    for offset, row in enumerate(breakout_and_rise, start=20):
        open_price, high, low, close, vol = row
        rows.append(
            {
                "trade_date": dates[offset].strftime("%Y%m%d"),
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "vol": vol,
                "amount": 600000,
                "turnover_rate": 2.0,
            }
        )

    final_closes = final_closes or [13.60, 13.40, 13.20, 13.05, 13.00]
    final_volumes = final_volumes or [1150, 1120, 1100, 1080, 1050]
    final_amounts = final_amounts or [600000, 600000, 600000, 600000, 600000]
    final_turnover_rates = final_turnover_rates or [2.0, 2.0, 2.0, 2.0, 2.0]

    for offset, low in enumerate(final_lows, start=35):
        close = final_closes[offset - 35]
        rows.append(
            {
                "trade_date": dates[offset].strftime("%Y%m%d"),
                "open": close + 0.10,
                "high": close + 0.20,
                "low": low,
                "close": close,
                "vol": final_volumes[offset - 35],
                "amount": final_amounts[offset - 35],
                "turnover_rate": final_turnover_rates[offset - 35],
            }
        )

    return pd.DataFrame(rows)


class StockFilterTest(unittest.TestCase):
    def test_passes_when_all_rules_match(self) -> None:
        result = evaluate_stock_filter(
            make_daily_frame(),
            stock_name="Ping An Bank",
            list_date="20000101",
            negative_announcement_dates=[],
        )
        self.assertTrue(result["passed"])
        self.assertTrue(all(result["checks"].values()))

    def test_fails_on_negative_announcement_day(self) -> None:
        result = evaluate_stock_filter(
            make_daily_frame(),
            stock_name="Ping An Bank",
            list_date="20000101",
            negative_announcement_dates=["20250121"],
        )
        self.assertFalse(result["passed"])
        self.assertFalse(result["checks"]["not_negative_announcement_day"])

    def test_fails_with_short_history(self) -> None:
        result = evaluate_stock_filter(
            make_daily_frame().tail(19),
            stock_name="Ping An Bank",
            list_date="20000101",
            negative_announcement_dates=[],
        )
        self.assertFalse(result["passed"])
        self.assertEqual(result["checks"], {"enough_history": False})

    def test_pullback_quality_passes(self) -> None:
        result = evaluate_pullback_quality(make_pullback_frame(final_lows=[13.9, 13.8, 13.6, 13.4, 13.2]))
        self.assertTrue(result["passed"])
        self.assertEqual(result["grade"], "pass")
        self.assertEqual(result["score"], 2)

    def test_pullback_quality_degrades_on_depth(self) -> None:
        result = evaluate_pullback_quality(make_pullback_frame(final_lows=[13.6, 13.2, 12.9, 12.7, 12.6]))
        self.assertFalse(result["passed"])
        self.assertEqual(result["grade"], "degraded")
        self.assertEqual(result["score"], 1)
        self.assertTrue(result["checks"]["depth_degraded"])

    def test_pullback_quality_excludes_on_ma20_break(self) -> None:
        result = evaluate_pullback_quality(
            make_pullback_frame(
                final_lows=[12.8, 11.8, 10.8, 10.1, 9.8],
                final_closes=[12.6, 11.6, 10.7, 10.0, 9.9],
                final_volumes=[1200, 1250, 1300, 2000, 2100],
            )
        )
        self.assertFalse(result["passed"])
        self.assertEqual(result["grade"], "excluded")
        self.assertFalse(result["checks"]["ma20_intact"])

    def test_volume_contraction_quality_passes(self) -> None:
        result = evaluate_volume_contraction_quality(
            make_pullback_frame(
                final_lows=[13.9, 13.8, 13.6, 13.4, 13.2],
                final_volumes=[760, 740, 720, 700, 680],
            )
        )
        self.assertTrue(result["passed"])
        self.assertEqual(result["grade"], "pass")
        self.assertEqual(result["score"], 2)

    def test_volume_contraction_quality_degrades_on_ratio(self) -> None:
        result = evaluate_volume_contraction_quality(
            make_pullback_frame(
                final_lows=[13.9, 13.8, 13.6, 13.4, 13.2],
                final_volumes=[1040, 1020, 1000, 980, 960],
            )
        )
        self.assertFalse(result["passed"])
        self.assertEqual(result["grade"], "degraded")
        self.assertEqual(result["score"], 1)
        self.assertTrue(result["checks"]["volume_contraction_acceptable"])

    def test_volume_contraction_quality_downgrades_fake_contraction(self) -> None:
        result = evaluate_volume_contraction_quality(
            make_pullback_frame(
                final_lows=[13.9, 13.8, 13.6, 13.4, 13.2],
                final_volumes=[760, 740, 720, 700, 680],
                final_amounts=[400000, 400000, 400000, 400000, 400000],
                final_turnover_rates=[0.8, 0.8, 0.8, 0.8, 0.8],
            )
        )
        self.assertFalse(result["passed"])
        self.assertEqual(result["grade"], "degraded")
        self.assertEqual(result["score"], 1)
        self.assertTrue(result["liquidity_warning"])


if __name__ == "__main__":
    unittest.main()
