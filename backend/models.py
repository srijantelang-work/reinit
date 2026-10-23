"""Domain models for wind forecast data."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


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
    """A matched pair of forecast and actual for a single target half-hour."""

    start_time: datetime
    forecast_mw: int | None = None
    forecast_publish_time: datetime | None = None
    actual_mw: int | None = None


class AccuracyMetrics(BaseModel):
    """Aggregated accuracy metrics over a set of forecast-actual pairs."""

    mae: float
    rmse: float
    bias: float
    point_count: int
    excluded_count: int


class DailyAccuracy(BaseModel):
    """Accuracy metrics aggregated for a single delivery day."""

    date: str
    mae: float
    rmse: float
    bias: float
    point_count: int
    excluded_count: int
