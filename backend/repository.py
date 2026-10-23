"""Data repository - loads the snapshot and provides typed access."""

from __future__ import annotations

import json
from pathlib import Path

from backend.config import settings
from backend.models import WindActual, WindForecast

_actuals: list[WindActual] = []
_forecasts: list[WindForecast] = []
_loaded: bool = False


def load_snapshot(path: str | None = None) -> None:
    """Load the JSON snapshot into module-level caches.

    Args:
        path: override path for testing; defaults to ``settings.data_snapshot_path``.
    """
    global _actuals, _forecasts, _loaded
    file_path = Path(path or settings.data_snapshot_path)
    if not file_path.exists():
        # Fallback: resolve relative to repository root if cwd is different (e.g. Vercel serverless)
        candidate = Path(__file__).resolve().parent.parent / file_path
        if candidate.exists():
            file_path = candidate
        else:
            _actuals = []
            _forecasts = []
            _loaded = True
            return

    raw = json.loads(file_path.read_text(encoding="utf-8"))
    _actuals = [WindActual(**row) for row in raw.get("actuals", [])]
    _forecasts = [WindForecast(**row) for row in raw.get("forecasts", [])]
    _loaded = True


def get_actuals() -> list[WindActual]:
    """Return all loaded wind actuals."""
    if not _loaded:
        load_snapshot()
    return _actuals


def get_forecasts() -> list[WindForecast]:
    """Return all loaded wind forecasts."""
    if not _loaded:
        load_snapshot()
    return _forecasts
