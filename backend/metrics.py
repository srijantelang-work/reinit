"""Accuracy metrics: MAE, RMSE, bias.

All metrics operate on forecast-actual pairs in MW.
Bias is defined as forecast minus actual (positive = over-forecast).
"""

from __future__ import annotations

import math


def mae(pairs: list[tuple[float, float]]) -> float:
    """Mean Absolute Error over (forecast, actual) pairs."""
    if not pairs:
        return 0.0
    return sum(abs(f - a) for f, a in pairs) / len(pairs)


def rmse(pairs: list[tuple[float, float]]) -> float:
    """Root Mean Square Error over (forecast, actual) pairs."""
    if not pairs:
        return 0.0
    return math.sqrt(sum((f - a) ** 2 for f, a in pairs) / len(pairs))


def bias(pairs: list[tuple[float, float]]) -> float:
    """Mean bias (forecast - actual) over pairs. Positive = over-forecast."""
    if not pairs:
        return 0.0
    return sum(f - a for f, a in pairs) / len(pairs)
