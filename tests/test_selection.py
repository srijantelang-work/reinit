"""Tests for the forecast selection logic."""

from __future__ import annotations

from datetime import datetime, timezone

from backend.selection import select_latest_forecast_before_cutoff


def _dt(iso: str) -> datetime:
    """Shorthand: parse an ISO string to a timezone-aware datetime."""
    return datetime.fromisoformat(iso).replace(tzinfo=timezone.utc)


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
            {
                "start_time": _dt("2026-01-02T00:00:00"),
                "publish_time": _dt("2026-01-01T10:00:00"),
                "generation_mw": 5000,
            },
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
            {
                "start_time": _dt("2026-01-02T00:00:00"),
                "publish_time": _dt("2026-01-01T09:00:00"),
                "generation_mw": 5000,
            },
        ]
        result = select_latest_forecast_before_cutoff(
            forecasts=forecasts,
            target_time=_dt("2026-01-02T00:00:00"),
            cutoff=_dt("2026-01-01T09:00:00"),
        )
        assert result is not None
        assert result["generation_mw"] == 5000

    def test_selects_latest_among_multiple(self) -> None:
        """When multiple forecasts qualify, pick the one with latest publish_time."""
        forecasts = [
            {
                "start_time": _dt("2026-01-02T06:00:00"),
                "publish_time": _dt("2026-01-01T03:30:00"),
                "generation_mw": 4000,
            },
            {
                "start_time": _dt("2026-01-02T06:00:00"),
                "publish_time": _dt("2026-01-01T05:30:00"),
                "generation_mw": 4500,
            },
            {
                "start_time": _dt("2026-01-02T06:00:00"),
                "publish_time": _dt("2026-01-01T08:30:00"),
                "generation_mw": 5000,
            },
            {
                "start_time": _dt("2026-01-02T06:00:00"),
                "publish_time": _dt("2026-01-01T10:30:00"),  # after cutoff
                "generation_mw": 5500,
            },
        ]
        result = select_latest_forecast_before_cutoff(
            forecasts=forecasts,
            target_time=_dt("2026-01-02T06:00:00"),
            cutoff=_dt("2026-01-01T09:00:00"),
        )
        assert result is not None
        assert result["generation_mw"] == 5000  # 08:30 publish, not 10:30

    def test_ignores_wrong_target_time(self) -> None:
        """Forecasts for a different target time should not be returned."""
        forecasts = [
            {
                "start_time": _dt("2026-01-02T12:00:00"),
                "publish_time": _dt("2026-01-01T05:00:00"),
                "generation_mw": 3000,
            },
        ]
        result = select_latest_forecast_before_cutoff(
            forecasts=forecasts,
            target_time=_dt("2026-01-02T06:00:00"),
            cutoff=_dt("2026-01-01T09:00:00"),
        )
        assert result is None
