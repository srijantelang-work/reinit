"""Tests for the forecast selection logic and cutoff computation."""

from __future__ import annotations

from datetime import date, datetime, timezone

from backend.models import WindActual, WindForecast
from backend.selection import (
    compute_cutoff_utc,
    match_forecasts_and_actuals,
    parse_date,
    select_latest_forecast_before_cutoff,
)


def _dt(iso: str) -> datetime:
    """Shorthand: parse an ISO string to a timezone-aware UTC datetime."""
    return datetime.fromisoformat(iso).replace(tzinfo=timezone.utc)


class TestCutoffComputation:
    """Verify D-1 cutoff calculation and Europe/London timezone handling."""

    def test_winter_gmt_cutoff(self) -> None:
        """In January, London is GMT (UTC+0). Cutoff 09:00 on D-1 is 09:00 UTC."""
        delivery = date(2026, 1, 2)
        cutoff_utc = compute_cutoff_utc(delivery, "09:00")
        assert cutoff_utc == _dt("2026-01-01T09:00:00")

    def test_winter_custom_cutoff(self) -> None:
        """Arbitrary cutoff times like 17:30 are computed correctly."""
        delivery = date(2026, 1, 15)
        cutoff_utc = compute_cutoff_utc(delivery, "17:30")
        assert cutoff_utc == _dt("2026-01-14T17:30:00")

    def test_summer_bst_dst_safe_conversion(self) -> None:
        """In July, London is BST (UTC+1). 09:00 BST corresponds to 08:00 UTC."""
        delivery = date(2026, 7, 2)
        cutoff_utc = compute_cutoff_utc(delivery, "09:00")
        # D-1 is July 1st, 09:00 BST -> 08:00 UTC
        assert cutoff_utc == _dt("2026-07-01T08:00:00")

    def test_parse_date(self) -> None:
        """Date parsing handles both strings and date objects."""
        assert parse_date("2026-01-02") == date(2026, 1, 2)
        assert parse_date(date(2026, 1, 2)) == date(2026, 1, 2)


class TestSelectLatestForecast:
    """Selection rule: latest publish_time <= cutoff for a given target time."""

    def test_no_forecasts_returns_none(self) -> None:
        result = select_latest_forecast_before_cutoff(
            forecasts=[],
            target_time=_dt("2026-01-02T00:00:00"),
            cutoff=_dt("2026-01-01T09:00:00"),
        )
        assert result is None

    def test_no_eligible_forecast_returns_none(self) -> None:
        """All forecasts published after the cutoff → no match."""
        forecasts = [
            WindForecast(
                start_time=_dt("2026-01-02T00:00:00"),
                publish_time=_dt("2026-01-01T10:00:00"),
                generation_mw=5000,
            ),
        ]
        result = select_latest_forecast_before_cutoff(
            forecasts=forecasts,
            target_time=_dt("2026-01-02T00:00:00"),
            cutoff=_dt("2026-01-01T09:00:00"),
        )
        assert result is None

    def test_exact_boundary_is_included(self) -> None:
        """Forecast published at exactly the cutoff time should be selected."""
        forecasts = [
            WindForecast(
                start_time=_dt("2026-01-02T00:00:00"),
                publish_time=_dt("2026-01-01T09:00:00"),
                generation_mw=5000,
            ),
        ]
        result = select_latest_forecast_before_cutoff(
            forecasts=forecasts,
            target_time=_dt("2026-01-02T00:00:00"),
            cutoff=_dt("2026-01-01T09:00:00"),
        )
        assert result is not None
        assert result.generation_mw == 5000

    def test_selects_latest_among_multiple(self) -> None:
        """When multiple forecasts qualify, pick the one with latest publish_time."""
        forecasts = [
            WindForecast(
                start_time=_dt("2026-01-02T06:00:00"),
                publish_time=_dt("2026-01-01T03:30:00"),
                generation_mw=4000,
            ),
            WindForecast(
                start_time=_dt("2026-01-02T06:00:00"),
                publish_time=_dt("2026-01-01T05:30:00"),
                generation_mw=4500,
            ),
            WindForecast(
                start_time=_dt("2026-01-02T06:00:00"),
                publish_time=_dt("2026-01-01T08:30:00"),
                generation_mw=5000,
            ),
            WindForecast(
                start_time=_dt("2026-01-02T06:00:00"),
                publish_time=_dt("2026-01-01T10:30:00"),  # after cutoff
                generation_mw=5500,
            ),
        ]
        result = select_latest_forecast_before_cutoff(
            forecasts=forecasts,
            target_time=_dt("2026-01-02T06:00:00"),
            cutoff=_dt("2026-01-01T09:00:00"),
        )
        assert result is not None
        assert result.generation_mw == 5000  # 08:30 publish, not 10:30

    def test_hourly_forecast_covers_half_hour(self) -> None:
        """An hourly forecast for 06:00 covers both 06:00 and 06:30."""
        forecasts = [
            WindForecast(
                start_time=_dt("2026-01-02T06:00:00"),
                publish_time=_dt("2026-01-01T08:30:00"),
                generation_mw=7200,
            ),
        ]
        # Query for 06:30 half-hour
        result = select_latest_forecast_before_cutoff(
            forecasts=forecasts,
            target_time=_dt("2026-01-02T06:30:00"),
            cutoff=_dt("2026-01-01T09:00:00"),
        )
        assert result is not None
        assert result.generation_mw == 7200

    def test_ignores_unrelated_target_time(self) -> None:
        """Forecast for 12:00 should not match 06:00."""
        forecasts = [
            WindForecast(
                start_time=_dt("2026-01-02T12:00:00"),
                publish_time=_dt("2026-01-01T05:00:00"),
                generation_mw=3000,
            ),
        ]
        result = select_latest_forecast_before_cutoff(
            forecasts=forecasts,
            target_time=_dt("2026-01-02T06:00:00"),
            cutoff=_dt("2026-01-01T09:00:00"),
        )
        assert result is None

    def test_naive_datetime_handling(self) -> None:
        """Naive datetimes for target_time and cutoff are safely treated as UTC."""
        forecasts = [
            WindForecast(
                start_time=_dt("2026-01-02T06:00:00"),
                publish_time=_dt("2026-01-01T08:00:00"),
                generation_mw=4500,
            ),
        ]
        naive_target = datetime(2026, 1, 2, 6, 0)
        naive_cutoff = datetime(2026, 1, 1, 9, 0)
        res = select_latest_forecast_before_cutoff(forecasts, naive_target, naive_cutoff)
        assert res is not None
        assert res.generation_mw == 4500


class TestMatchForecastsAndActuals:
    """Verify daily pairing across all 48 settlement periods."""

    def test_pairs_all_48_periods(self) -> None:
        delivery = date(2026, 1, 2)
        cutoff = _dt("2026-01-01T09:00:00")

        # Supply 1 actual and 1 forecast
        actuals = [
            WindActual(
                settlement_date="2026-01-02",
                settlement_period=1,
                start_time=_dt("2026-01-02T00:00:00"),
                publish_time=_dt("2026-01-02T00:30:00"),
                generation_mw=10000,
            )
        ]
        forecasts = [
            WindForecast(
                start_time=_dt("2026-01-02T00:00:00"),
                publish_time=_dt("2026-01-01T08:30:00"),
                generation_mw=9500,
            )
        ]

        pairs = match_forecasts_and_actuals(delivery, cutoff, actuals, forecasts)
        assert len(pairs) == 48

        # First pair has both forecast and actual
        p1 = pairs[0]
        assert p1.start_time == _dt("2026-01-02T00:00:00")
        assert p1.forecast_mw == 9500
        assert p1.actual_mw == 10000

        # Subsequent periods without actuals have actual_mw=None
        p2 = pairs[1]
        assert p2.start_time == _dt("2026-01-02T00:30:00")
        assert p2.actual_mw is None
        # Hourly forecast for 00:00 also covers 00:30
        assert p2.forecast_mw == 9500
