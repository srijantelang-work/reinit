"""Unit tests for configuration loading and CORS parsing in backend/config.py."""

import os
from backend.config import Settings


def test_cors_origins_default_wildcard() -> None:
    """Verify default CORS origin is wildcard list."""
    os.environ.pop("CORS_ORIGINS", None)
    s = Settings()
    assert s.cors_origins == ["*"]


def test_cors_origins_bare_asterisk() -> None:
    """Verify bare asterisk from Render/cloud env vars parses to list containing '*'."""
    os.environ["CORS_ORIGINS"] = "*"
    s = Settings()
    assert s.cors_origins == ["*"]


def test_cors_origins_comma_separated_urls() -> None:
    """Verify comma-separated URLs parse cleanly without spaces."""
    os.environ["CORS_ORIGINS"] = "https://app.vercel.app, http://localhost:5173"
    s = Settings()
    assert s.cors_origins == ["https://app.vercel.app", "http://localhost:5173"]


def test_cors_origins_json_array_format() -> None:
    """Verify JSON array strings parse correctly."""
    os.environ["CORS_ORIGINS"] = '["https://portal.vercel.app"]'
    s = Settings()
    assert s.cors_origins == ["https://portal.vercel.app"]
