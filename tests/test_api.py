"""Tests for FastAPI endpoints: /api/health, /api/meta, /api/forecast, /api/accuracy."""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app import app
from backend.repository import load_snapshot

client = TestClient(app)


class TestApiHealth:
    """Health check tests."""

    def test_health_ok(self) -> None:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_security_headers_present(self) -> None:
        response = client.get("/api/health")
        assert response.headers.get("x-content-type-options") == "nosniff"
        assert response.headers.get("x-frame-options") == "DENY"
        assert response.headers.get("referrer-policy") == "strict-origin-when-cross-origin"


class TestApiMeta:
    """Metadata endpoint tests."""

    def test_meta_returns_correct_structure(self) -> None:
        load_snapshot()
        response = client.get("/api/meta")
        assert response.status_code == 200
        data = response.json()

        assert data["start_date"] == "2026-01-02"
        assert data["end_date"] == "2026-02-01"
        assert data["default_cutoff"] == "09:00"
        assert data["default_date"] == "2026-01-02"
        assert data["total_actual_records"] == 1488
        assert data["total_forecast_records"] > 10000


class TestApiForecast:
    """Forecast series endpoint tests."""

    def test_forecast_happy_path(self) -> None:
        load_snapshot()
        response = client.get("/api/forecast?delivery_date=2026-01-02&cutoff=09:00")
        assert response.status_code == 200
        data = response.json()

        assert data["delivery_date"] == "2026-01-02"
        assert data["cutoff"] == "09:00"
        assert data["cutoff_utc"] == "2026-01-01T09:00:00Z"

        points = data["points"]
        assert len(points) == 48

        # First settlement period
        p1 = points[0]
        assert p1["settlement_period"] == 1
        assert p1["actual_mw"] == 15228
        assert p1["forecast_mw"] is not None
        assert p1["forecast_publish_time"] is not None

    def test_forecast_missing_delivery_date(self) -> None:
        response = client.get("/api/forecast")
        assert response.status_code == 422

    def test_forecast_invalid_date_format(self) -> None:
        response = client.get("/api/forecast?delivery_date=2026/01/02")
        assert response.status_code == 400
        assert "Invalid date format" in response.json()["detail"]

    def test_forecast_out_of_range_date(self) -> None:
        response = client.get("/api/forecast?delivery_date=2025-12-31")
        assert response.status_code == 400
        assert "out of range" in response.json()["detail"]

    def test_forecast_invalid_cutoff(self) -> None:
        response = client.get("/api/forecast?delivery_date=2026-01-02&cutoff=25:00")
        assert response.status_code == 400
        assert "Invalid cutoff format" in response.json()["detail"]

    def test_forecast_custom_cutoff(self) -> None:
        response = client.get("/api/forecast?delivery_date=2026-01-02&cutoff=14:30")
        assert response.status_code == 200
        assert response.json()["cutoff_utc"] == "2026-01-01T14:30:00Z"


class TestApiAccuracy:
    """Accuracy metrics endpoint tests."""

    def test_accuracy_happy_path(self) -> None:
        load_snapshot()
        # Single day
        response = client.get("/api/accuracy?start=2026-01-02&end=2026-01-02&cutoff=09:00")
        assert response.status_code == 200
        data = response.json()

        assert data["start_date"] == "2026-01-02"
        assert data["end_date"] == "2026-01-02"
        assert data["cutoff"] == "09:00"

        metrics = data["metrics"]
        assert metrics["point_count"] == 48
        assert metrics["excluded_count"] == 0
        assert metrics["mae"] > 0
        assert metrics["rmse"] > 0

        daily = data["daily"]
        assert len(daily) == 1
        assert daily[0]["date"] == "2026-01-02"

    def test_accuracy_multi_day(self) -> None:
        load_snapshot()
        # 3 days: Jan 2 to Jan 4
        response = client.get("/api/accuracy?start=2026-01-02&end=2026-01-04&cutoff=09:00")
        assert response.status_code == 200
        data = response.json()

        assert data["metrics"]["point_count"] == 48 * 3
        assert len(data["daily"]) == 3
        assert [d["date"] for d in data["daily"]] == [
            "2026-01-02",
            "2026-01-03",
            "2026-01-04",
        ]

    def test_accuracy_start_after_end(self) -> None:
        response = client.get("/api/accuracy?start=2026-01-05&end=2026-01-02")
        assert response.status_code == 400
        assert "cannot be after end date" in response.json()["detail"]

    def test_accuracy_out_of_range(self) -> None:
        response = client.get("/api/accuracy?start=2025-12-01&end=2026-01-05")
        assert response.status_code == 400
        assert "outside available range" in response.json()["detail"]

    def test_accuracy_invalid_cutoff(self) -> None:
        response = client.get("/api/accuracy?start=2026-01-02&end=2026-01-03&cutoff=abc")
        assert response.status_code == 400
        assert "Invalid cutoff format" in response.json()["detail"]
