"""Application configuration loaded from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with defaults suitable for local development."""

    cors_origins: list[str] = ["http://localhost:5173"]
    log_level: str = "INFO"
    data_snapshot_path: str = "data/snapshot.json"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
