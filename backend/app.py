"""FastAPI application factory and API endpoints."""

from __future__ import annotations

import re
from datetime import date, timedelta
from typing import TYPE_CHECKING

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

from backend.config import settings
from backend.metrics import calculate_daily_metrics, calculate_metrics
from backend.models import (
    AccuracyResponse,
    ForecastPoint,
    ForecastResponse,
    MetaResponse,
)
from backend.repository import get_actuals, get_forecasts
from backend.selection import compute_cutoff_utc, match_forecasts_and_actuals

app = FastAPI(
    title="Wind Forecast Portal",
    description="UK wind forecast accuracy dashboard - backend API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Attach standard HTTP security headers to all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


def _validate_cutoff(cutoff: str) -> None:
    """Validate that cutoff string matches HH:MM format (00:00 to 23:59)."""
    if not re.match(r"^([01]\d|2[0-3]):([0-5]\d)$", cutoff):
        raise HTTPException(
            status_code=400,
            detail="Invalid cutoff format. Expected HH:MM between 00:00 and 23:59 (e.g. '09:00').",
        )


def _validate_date(date_str: str) -> date:
    """Parse date string YYYY-MM-DD or raise HTTPException 400."""
    try:
        return date.fromisoformat(date_str)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format '{date_str}'. Expected YYYY-MM-DD.",
        ) from exc


def _get_data_bounds() -> tuple[date, date]:
    """Retrieve min and max delivery dates available in the repository snapshot."""
    actuals = get_actuals()
    if not actuals:
        # Fallback to configured January window
        return date(2026, 1, 2), date(2026, 2, 1)
    dates = sorted({a.settlement_date for a in actuals})
    return date.fromisoformat(dates[0]), date.fromisoformat(dates[-1])


@app.get("/api/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/api/meta", response_model=MetaResponse)
async def get_meta() -> MetaResponse:
    """Return available date range, default values, and snapshot statistics."""
    min_date, max_date = _get_data_bounds()
    actuals = get_actuals()
    forecasts = get_forecasts()

    return MetaResponse(
        start_date=min_date.isoformat(),
        end_date=max_date.isoformat(),
        default_cutoff="09:00",
        default_date=min_date.isoformat(),
        total_actual_records=len(actuals),
        total_forecast_records=len(forecasts),
    )


@app.get("/api/forecast", response_model=ForecastResponse)
async def get_forecast(
    delivery_date: str = Query(..., description="Target delivery date (YYYY-MM-DD)"),
    cutoff: str = Query("09:00", description="D-1 decision cutoff time (HH:MM)"),
) -> ForecastResponse:
    """Return the half-hourly forecast vs actual series for a delivery date and cutoff."""
    _validate_cutoff(cutoff)
    d_date = _validate_date(delivery_date)
    min_date, max_date = _get_data_bounds()

    if d_date < min_date or d_date > max_date:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Delivery date {delivery_date} is out of range. "
                f"Available range is {min_date.isoformat()} to {max_date.isoformat()}."
            ),
        )

    actuals = get_actuals()
    forecasts = get_forecasts()

    cutoff_utc = compute_cutoff_utc(d_date, cutoff)
    pairs = match_forecasts_and_actuals(d_date, cutoff_utc, actuals, forecasts)

    points = [
        ForecastPoint(
            settlement_period=idx + 1,
            start_time=p.start_time.isoformat().replace("+00:00", "Z"),
            forecast_mw=p.forecast_mw,
            forecast_publish_time=(
                p.forecast_publish_time.isoformat().replace("+00:00", "Z")
                if p.forecast_publish_time
                else None
            ),
            actual_mw=p.actual_mw,
        )
        for idx, p in enumerate(pairs)
    ]

    return ForecastResponse(
        delivery_date=d_date.isoformat(),
        cutoff=cutoff,
        cutoff_utc=cutoff_utc.isoformat().replace("+00:00", "Z"),
        points=points,
    )


@app.get("/api/accuracy", response_model=AccuracyResponse)
async def get_accuracy(
    start: str = Query(..., description="Start delivery date (YYYY-MM-DD)"),
    end: str = Query(..., description="End delivery date (YYYY-MM-DD)"),
    cutoff: str = Query("09:00", description="D-1 decision cutoff time (HH:MM)"),
) -> AccuracyResponse:
    """Return aggregated and daily accuracy metrics across a date range and cutoff."""
    _validate_cutoff(cutoff)
    start_date = _validate_date(start)
    end_date = _validate_date(end)

    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail=f"Start date '{start}' cannot be after end date '{end}'.",
        )

    min_date, max_date = _get_data_bounds()
    if start_date < min_date or end_date > max_date:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Requested date range ({start} to {end}) extends outside available range "
                f"({min_date.isoformat()} to {max_date.isoformat()})."
            ),
        )

    actuals = get_actuals()
    forecasts = get_forecasts()

    all_pairs = []
    current = start_date
    while current <= end_date:
        cutoff_utc = compute_cutoff_utc(current, cutoff)
        day_pairs = match_forecasts_and_actuals(current, cutoff_utc, actuals, forecasts)
        all_pairs.extend(day_pairs)
        current += timedelta(days=1)

    overall_metrics = calculate_metrics(all_pairs)
    daily_metrics = calculate_daily_metrics(all_pairs)

    return AccuracyResponse(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        cutoff=cutoff,
        metrics=overall_metrics,
        daily=daily_metrics,
    )
