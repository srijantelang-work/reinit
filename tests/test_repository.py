"""Tests for the data repository and snapshot loading."""

from __future__ import annotations

from typing import TYPE_CHECKING

from backend.repository import get_actuals, get_forecasts, load_snapshot

if TYPE_CHECKING:
    from pathlib import Path


class TestRepository:
    """Verify loading from snapshot and typed object access."""

    def test_load_real_snapshot(self) -> None:
        """Loads snapshot from data/snapshot.json and checks record counts."""
        load_snapshot()
        actuals = get_actuals()
        forecasts = get_forecasts()

        # Jan 2 to Feb 1 has 31 days * 48 periods = 1488 actuals
        assert len(actuals) == 1488
        assert len(forecasts) > 10000

        # Verify typed attributes
        first_act = actuals[0]
        assert first_act.settlement_date == "2026-01-02"
        assert first_act.settlement_period == 1
        assert isinstance(first_act.generation_mw, int)

        first_fc = forecasts[0]
        assert isinstance(first_fc.generation_mw, int)
        assert first_fc.start_time is not None

    def test_load_nonexistent_file(self, tmp_path: Path) -> None:
        """Loading a non-existent file cleanly resets caches to empty lists."""
        dummy_path = tmp_path / "nonexistent.json"
        load_snapshot(str(dummy_path))

        assert get_actuals() == []
        assert get_forecasts() == []

        # Reload the real snapshot afterwards
        load_snapshot()
        assert len(get_actuals()) == 1488

    def test_lazy_auto_loading(self) -> None:
        """Calling get_actuals/get_forecasts when not loaded automatically triggers load_snapshot."""
        import backend.repository as repo

        repo._loaded = False
        repo._actuals = []
        repo._forecasts = []

        assert len(repo.get_actuals()) == 1488
        assert len(repo.get_forecasts()) > 10000
