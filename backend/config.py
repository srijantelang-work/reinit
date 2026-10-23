"""Application configuration loaded from environment variables."""

from __future__ import annotations

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with defaults suitable for cloud and local development."""

    cors_origins: list[str] = ["*"]
    log_level: str = "INFO"
    data_snapshot_path: str = "data/snapshot.json"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: object) -> list[str]:
        """Allow CORS_ORIGINS as a JSON list, comma-separated string, or wildcard."""
        if isinstance(v, str):
            v_str = v.strip()
            if v_str.startswith("[") and v_str.endswith("]"):
                import json
                return json.loads(v_str)
            return [origin.strip() for origin in v_str.split(",") if origin.strip()]
        if isinstance(v, list):
            return [str(item) for item in v]
        return ["*"]


settings = Settings()
