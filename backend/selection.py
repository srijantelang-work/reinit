"""Forecast selection logic.

For each target half-hour on delivery day D, select the forecast with the
greatest publishTime that is at or before the cutoff on D-1.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


def select_latest_forecast_before_cutoff(
    forecasts: list[dict[str, object]],
    target_time: datetime,
    cutoff: datetime,
) -> dict[str, object] | None:
    """Return the forecast for *target_time* with the latest publishTime <= cutoff.

    Args:
        forecasts: list of forecast dicts with keys ``start_time`` and ``publish_time``.
        target_time: the delivery half-hour to match.
        cutoff: the decision deadline (publish_time must be <= this).

    Returns:
        The best-matching forecast dict, or ``None`` if no eligible forecast exists.
    """
    eligible = [
        f
        for f in forecasts
        if f["start_time"] == target_time and f["publish_time"] <= cutoff  # type: ignore[operator]
    ]
    if not eligible:
        return None
    return max(eligible, key=lambda f: f["publish_time"])  # type: ignore[arg-type,return-value]
