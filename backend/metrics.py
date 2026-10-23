"""Accuracy metrics: MAE, RMSE, bias, daily aggregation, and exclusion counting.

All metrics operate on forecast-actual pairs in MW.
Bias is defined as forecast minus actual (positive = over-forecast).
Half-hours with no eligible forecast or missing actual are excluded,
and the excluded count is recorded.
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import TYPE_CHECKING

from backend.models import AccuracyMetrics, DailyAccuracy, ForecastActualPair

if TYPE_CHECKING:
    from collections.abc import Sequence


def mae(pairs: Sequence[tuple[float, float]]) -> float:
    """Mean Absolute Error over (forecast, actual) pairs in MW."""
    if not pairs:
        return 0.0
    return sum(abs(f - a) for f, a in pairs) / len(pairs)


def rmse(pairs: Sequence[tuple[float, float]]) -> float:
    """Root Mean Square Error over (forecast, actual) pairs in MW."""
    if not pairs:
        return 0.0
    return math.sqrt(sum((f - a) ** 2 for f, a in pairs) / len(pairs))


def bias(pairs: Sequence[tuple[float, float]]) -> float:
    """Mean bias (forecast - actual) over pairs in MW. Positive = over-forecast."""
    if not pairs:
        return 0.0
    return sum(f - a for f, a in pairs) / len(pairs)


def calculate_metrics(pairs: Sequence[ForecastActualPair]) -> AccuracyMetrics:
    """Calculate aggregated MAE, RMSE, bias, point count, and excluded count.

    Pairs where either forecast_mw or actual_mw is None are excluded from
    the error calculations and counted under excluded_count.

    Args:
        pairs: Sequence of ForecastActualPair objects.

    Returns:
        AccuracyMetrics with computed values rounded to 2 decimal places.
    """
    valid_pairs: list[tuple[float, float]] = []
    excluded = 0

    for p in pairs:
        if p.forecast_mw is not None and p.actual_mw is not None:
            valid_pairs.append((float(p.forecast_mw), float(p.actual_mw)))
        else:
            excluded += 1

    if not valid_pairs:
        return AccuracyMetrics(
            mae=0.0,
            rmse=0.0,
            bias=0.0,
            point_count=0,
            excluded_count=excluded,
        )

    return AccuracyMetrics(
        mae=round(mae(valid_pairs), 2),
        rmse=round(rmse(valid_pairs), 2),
        bias=round(bias(valid_pairs), 2),
        point_count=len(valid_pairs),
        excluded_count=excluded,
    )


def calculate_daily_metrics(pairs: Sequence[ForecastActualPair]) -> list[DailyAccuracy]:
    """Group pairs by delivery date and calculate daily accuracy metrics.

    Args:
        pairs: Sequence of ForecastActualPair objects across one or more days.

    Returns:
        List of DailyAccuracy objects sorted by date.
    """
    by_date: dict[str, list[ForecastActualPair]] = defaultdict(list)
    for p in pairs:
        d_str = p.start_time.strftime("%Y-%m-%d")
        by_date[d_str].append(p)

    results: list[DailyAccuracy] = []
    for d_str in sorted(by_date.keys()):
        day_pairs = by_date[d_str]
        m = calculate_metrics(day_pairs)
        results.append(
            DailyAccuracy(
                date=d_str,
                mae=m.mae,
                rmse=m.rmse,
                bias=m.bias,
                point_count=m.point_count,
                excluded_count=m.excluded_count,
            )
        )

    return results
