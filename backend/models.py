"""Domain and API models for wind forecast data."""

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


# API Schemas


class MetaResponse(BaseModel):
    """Metadata about available data range and configuration defaults."""

    start_date: str
    end_date: str
    default_cutoff: str
    default_date: str
    total_actual_records: int
    total_forecast_records: int


class ForecastPoint(BaseModel):
    """A single half-hour point in the daily forecast series."""

    settlement_period: int
    start_time: str
    forecast_mw: int | None = None
    forecast_publish_time: str | None = None
    actual_mw: int | None = None


class ForecastResponse(BaseModel):
    """Forecast series response for a delivery day and cutoff."""

    delivery_date: str
    cutoff: str
    cutoff_utc: str
    points: list[ForecastPoint]


class AccuracyResponse(BaseModel):
    """Accuracy metrics response across a date range and cutoff."""

    start_date: str
    end_date: str
    cutoff: str
    metrics: AccuracyMetrics
    daily: list[DailyAccuracy]
