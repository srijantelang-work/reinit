"""Tests for the Vercel serverless entrypoint api/index.py."""

from fastapi.testclient import TestClient

from api.index import app, handler


def test_vercel_entrypoint_exports_app_and_handler() -> None:
    """Verify that both app and handler are exposed for ASGI servers."""
    assert app is not None
    assert handler is app


def test_vercel_entrypoint_serves_health() -> None:
    """Verify TestClient can call the entrypoint."""
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_vercel_entrypoint_serves_meta() -> None:
    """Verify metadata is loaded properly through the entrypoint."""
    client = TestClient(app)
    response = client.get("/api/meta")
    assert response.status_code == 200
    data = response.json()
    assert "start_date" in data
    assert "default_cutoff" in data
