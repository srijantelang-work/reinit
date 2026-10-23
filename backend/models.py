"""Domain models for wind forecast data."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import datetime


class WindActual(BaseModel):
    """Half-hourly actual wind generation from FUELHH."""

    settlement_date: str
    settlement_period: int
    start_time: datetime
    publish_time: datetime
    generation_mw: int


class WindForecast(BaseModel):
    """Wind generation forecast from WINDFOR."""

    start_time: datetime
    publish_time: datetime
    generation_mw: int


class ForecastActualPair(BaseModel):
    """A matched pair of forecast and actual for a single target time."""

    start_time: datetime
    forecast_mw: int
    forecast_publish_time: datetime
    actual_mw: int | None = None


class AccuracyMetrics(BaseModel):
    """Aggregated accuracy metrics over a set of forecast-actual pairs."""

    mae: float
    rmse: float
    bias: float
    point_count: int
    excluded_count: int
