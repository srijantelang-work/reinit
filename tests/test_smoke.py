"""Smoke tests: app imports, health endpoint, and metric functions."""

from __future__ import annotations

import math

from fastapi.testclient import TestClient

from backend.app import app
from backend.metrics import bias, mae, rmse

client = TestClient(app)


class TestHealthEndpoint:
    """Health endpoint should return 200 with status ok."""

    def test_health_returns_ok(self) -> None:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestMetrics:
    """Basic metric calculations."""

    def test_mae_empty(self) -> None:
        assert mae([]) == 0.0

    def test_mae_simple(self) -> None:
        pairs = [(100.0, 80.0), (200.0, 210.0)]
        # |100-80| = 20, |200-210| = 10  →  mean = 15
        assert mae(pairs) == 15.0

    def test_rmse_empty(self) -> None:
        assert rmse([]) == 0.0

    def test_rmse_simple(self) -> None:
        pairs = [(100.0, 80.0), (200.0, 210.0)]
        # (20^2 + 10^2) / 2 = 250  →  sqrt = 15.811...
        expected = math.sqrt(250)
        assert abs(rmse(pairs) - expected) < 1e-6

    def test_bias_empty(self) -> None:
        assert bias([]) == 0.0

    def test_bias_positive_means_overforecast(self) -> None:
        pairs = [(100.0, 80.0), (200.0, 210.0)]
        # (20 + -10) / 2 = 5.0
        assert bias(pairs) == 5.0

    def test_perfect_forecast(self) -> None:
        pairs = [(100.0, 100.0), (200.0, 200.0)]
        assert mae(pairs) == 0.0
        assert rmse(pairs) == 0.0
        assert bias(pairs) == 0.0
