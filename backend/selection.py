"""Forecast selection and cutoff computation logic.

Rules:
1. For delivery day D, decisions are made on D-1.
2. The decision cutoff is interpreted in Europe/London timezone.
3. For each target half-hour on delivery day D, use the forecast with the
   greatest publish_time at or before the cutoff on D-1.
4. If an hourly forecast is provided, it covers both half-hours within that hour.
5. If no forecast is published at or before the cutoff, the target time has no
   eligible forecast and is excluded from metrics.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from backend.models import ForecastActualPair, WindActual, WindForecast

LONDON_TZ = ZoneInfo("Europe/London")


def compute_cutoff_utc(delivery_date: date, cutoff_time_str: str = "09:00") -> datetime:
    """Compute the decision cutoff timestamp in UTC for a given delivery date.

    The decision takes place on D-1. The cutoff time is interpreted in
    Europe/London timezone, handling GMT/BST transitions cleanly.

    Args:
        delivery_date: The target delivery date (Day D).
        cutoff_time_str: The cutoff time in HH:MM format (default: "09:00").

    Returns:
        Timezone-aware datetime in UTC representing the cutoff deadline.
    """
    decision_date = delivery_date - timedelta(days=1)
    hour, minute = map(int, cutoff_time_str.split(":"))
    cutoff_time = time(hour=hour, minute=minute)

    # Construct datetime in Europe/London timezone
    local_dt = datetime.combine(decision_date, cutoff_time).replace(tzinfo=LONDON_TZ)

    # Convert to UTC
    return local_dt.astimezone(timezone.utc)


def parse_date(val: str | date) -> date:
    """Parse string YYYY-MM-DD or date object to date."""
    if isinstance(val, date):
        return val
    return date.fromisoformat(val)


def select_latest_forecast_before_cutoff(
    forecasts: list[WindForecast],
    target_time: datetime,
    cutoff: datetime,
) -> WindForecast | None:
    """Select the latest forecast for target_time published at or before cutoff.

    Matches either an exact target_time, or an hourly forecast whose hour
    window [start_time, start_time + 1h) covers target_time.

    Args:
        forecasts: Collection of WindForecast objects.
        target_time: The delivery target half-hour (UTC).
        cutoff: The decision deadline (UTC).

    Returns:
        The eligible WindForecast with the greatest publish_time, or None.
    """
    # Ensure UTC timezone awareness
    if target_time.tzinfo is None:
        target_time = target_time.replace(tzinfo=timezone.utc)
    if cutoff.tzinfo is None:
        cutoff = cutoff.replace(tzinfo=timezone.utc)

    one_hour = timedelta(hours=1)
    eligible: list[WindForecast] = []

    for f in forecasts:
        f_st = f.start_time if f.start_time.tzinfo else f.start_time.replace(tzinfo=timezone.utc)
        f_pt = (
            f.publish_time if f.publish_time.tzinfo else f.publish_time.replace(tzinfo=timezone.utc)
        )

        # Publish time must be <= cutoff
        if f_pt > cutoff:
            continue

        # Check coverage: exact match or containing hour [f_st, f_st + 1h)
        if f_st == target_time or (f_st <= target_time < f_st + one_hour):
            eligible.append(f)

    if not eligible:
        return None

    return max(
        eligible,
        key=lambda f: (
            f.publish_time.replace(tzinfo=timezone.utc)
            if f.publish_time.tzinfo is None
            else f.publish_time
        ),
    )


def match_forecasts_and_actuals(
    target_date: date,
    cutoff_utc: datetime,
    actuals: list[WindActual],
    forecasts: list[WindForecast],
) -> list[ForecastActualPair]:
    """Pair each half-hour of target_date with the selected forecast and actual.

    Args:
        target_date: The delivery date (Day D).
        cutoff_utc: Decision deadline in UTC.
        actuals: Loaded actuals records.
        forecasts: Loaded forecasts records.

    Returns:
        List of 48 ForecastActualPair objects for the delivery day.
    """
    # Filter actuals for this delivery date
    date_str = target_date.isoformat()
    day_actuals = {a.settlement_period: a for a in actuals if a.settlement_date == date_str}

    pairs: list[ForecastActualPair] = []

    # UK standard delivery day has 48 settlement periods
    # Period 1 is 00:00 to 00:30 UTC
    day_start = datetime.combine(target_date, time(0, 0), tzinfo=timezone.utc)

    for period in range(1, 49):
        target_time = day_start + timedelta(minutes=(period - 1) * 30)

        selected_fc = select_latest_forecast_before_cutoff(forecasts, target_time, cutoff_utc)
        act = day_actuals.get(period)

        if selected_fc is not None:
            pairs.append(
                ForecastActualPair(
                    start_time=target_time,
                    forecast_mw=selected_fc.generation_mw,
                    forecast_publish_time=selected_fc.publish_time,
                    actual_mw=act.generation_mw if act else None,
                )
            )
        else:
            # No eligible forecast found
            pairs.append(
                ForecastActualPair(
                    start_time=target_time,
                    forecast_mw=None,
                    forecast_publish_time=None,
                    actual_mw=act.generation_mw if act else None,
                )
            )

    return pairs
