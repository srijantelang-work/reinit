"""Tests for MAE, RMSE, bias, exclusion counts, and daily aggregation."""

from __future__ import annotations

import math
from datetime import datetime, timezone

from backend.metrics import bias, calculate_daily_metrics, calculate_metrics, mae, rmse
from backend.models import ForecastActualPair


def _dt(iso: str) -> datetime:
    return datetime.fromisoformat(iso).replace(tzinfo=timezone.utc)


class TestBasicMetrics:
    """Verify pure metric functions against hand-computed values and edge cases."""

    def test_empty_inputs(self) -> None:
        assert mae([]) == 0.0
        assert rmse([]) == 0.0
        assert bias([]) == 0.0

    def test_hand_computed_values(self) -> None:
        """Hand calculation:
        Pair 1: f=100, a=80   -> err = +20, |err| = 20, sq = 400
        Pair 2: f=200, a=210  -> err = -10, |err| = 10, sq = 100
        Pair 3: f=300, a=270  -> err = +30, |err| = 30, sq = 900

        MAE  = (20 + 10 + 30) / 3 = 60 / 3 = 20.0
        RMSE = sqrt((400 + 100 + 900) / 3) = sqrt(1400 / 3) = sqrt(466.6667) = 21.6024...
        Bias = (20 - 10 + 30) / 3 = 40 / 3 = 13.3333...
        """
        pairs = [(100.0, 80.0), (200.0, 210.0), (300.0, 270.0)]

        assert mae(pairs) == 20.0
        assert abs(rmse(pairs) - math.sqrt(1400.0 / 3.0)) < 1e-6
        assert abs(bias(pairs) - (40.0 / 3.0)) < 1e-6

    def test_perfect_prediction(self) -> None:
        pairs = [(500.0, 500.0), (1200.0, 1200.0)]
        assert mae(pairs) == 0.0
        assert rmse(pairs) == 0.0
        assert bias(pairs) == 0.0

    def test_underforecast_negative_bias(self) -> None:
        """Forecast consistently lower than actual results in negative bias."""
        pairs = [(100.0, 150.0), (200.0, 250.0)]
        assert bias(pairs) == -50.0
        assert mae(pairs) == 50.0


class TestCalculateMetrics:
    """Verify pair aggregation, rounding, and exclusion counting."""

    def test_empty_pairs(self) -> None:
        m = calculate_metrics([])
        assert m.mae == 0.0
        assert m.rmse == 0.0
        assert m.bias == 0.0
        assert m.point_count == 0
        assert m.excluded_count == 0

    def test_all_excluded(self) -> None:
        pairs = [
            ForecastActualPair(start_time=_dt("2026-01-02T00:00:00"), forecast_mw=None, actual_mw=100),
            ForecastActualPair(start_time=_dt("2026-01-02T00:30:00"), forecast_mw=200, actual_mw=None),
            ForecastActualPair(start_time=_dt("2026-01-02T01:00:00"), forecast_mw=None, actual_mw=None),
        ]
        m = calculate_metrics(pairs)
        assert m.point_count == 0
        assert m.excluded_count == 3
        assert m.mae == 0.0

    def test_mixed_valid_and_excluded(self) -> None:
        pairs = [
            # Valid: 100 vs 80 -> err = +20
            ForecastActualPair(start_time=_dt("2026-01-02T00:00:00"), forecast_mw=100, actual_mw=80),
            # Valid: 200 vs 210 -> err = -10
            ForecastActualPair(start_time=_dt("2026-01-02T00:30:00"), forecast_mw=200, actual_mw=210),
            # Excluded: missing actual
            ForecastActualPair(start_time=_dt("2026-01-02T01:00:00"), forecast_mw=300, actual_mw=None),
            # Excluded: missing forecast
            ForecastActualPair(start_time=_dt("2026-01-02T01:30:00"), forecast_mw=None, actual_mw=400),
        ]
        m = calculate_metrics(pairs)
        assert m.point_count == 2
        assert m.excluded_count == 2
        # MAE = (20 + 10) / 2 = 15.0
        assert m.mae == 15.0
        # Bias = (20 - 10) / 2 = 5.0
        assert m.bias == 5.0
        # RMSE = sqrt((400 + 100) / 2) = sqrt(250) = 15.81
        assert m.rmse == 15.81


class TestCalculateDailyMetrics:
    """Verify daily aggregation across multiple delivery days."""

    def test_daily_aggregation(self) -> None:
        pairs = [
            # Day 1: 2026-01-02
            ForecastActualPair(start_time=_dt("2026-01-02T00:00:00"), forecast_mw=100, actual_mw=80),
            ForecastActualPair(start_time=_dt("2026-01-02T00:30:00"), forecast_mw=200, actual_mw=200),
            # Day 2: 2026-01-03
            ForecastActualPair(start_time=_dt("2026-01-03T00:00:00"), forecast_mw=300, actual_mw=350),
            ForecastActualPair(start_time=_dt("2026-01-03T00:30:00"), forecast_mw=None, actual_mw=400),
        ]

        daily = calculate_daily_metrics(pairs)
        assert len(daily) == 2

        # Day 1
        d1 = daily[0]
        assert d1.date == "2026-01-02"
        assert d1.point_count == 2
        assert d1.excluded_count == 0
        assert d1.mae == 10.0  # (|20| + 0) / 2
        assert d1.bias == 10.0  # (+20 + 0) / 2

        # Day 2
        d2 = daily[1]
        assert d2.date == "2026-01-03"
        assert d2.point_count == 1
        assert d2.excluded_count == 1
        assert d2.mae == 50.0  # |300 - 350|
        assert d2.bias == -50.0
