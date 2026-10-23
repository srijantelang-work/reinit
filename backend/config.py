import json
import logging
import os
from typing import Union

from pydantic import field_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger("backend.config")


class Settings(BaseSettings):
    """Application settings with defaults suitable for cloud and local development."""

    cors_origins: Union[list[str], str] = ["*"]
    log_level: str = "INFO"
    data_snapshot_path: str = "data/snapshot.json"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    @field_validator("cors_origins", mode="after")
    @classmethod
    def normalize_cors_origins(cls, v: Union[list[str], str]) -> list[str]:
        """Normalize CORS_ORIGINS from wildcard, comma-separated string, or JSON list."""
        if isinstance(v, str):
            v_str = v.strip()
            if v_str == "*":
                return ["*"]
            if v_str.startswith("[") and v_str.endswith("]"):
                try:
                    parsed = json.loads(v_str)
                    if isinstance(parsed, list):
                        return [str(x) for x in parsed]
                except Exception:
                    pass
            return [origin.strip() for origin in v_str.split(",") if origin.strip()]
        return [str(item) for item in v]


settings = Settings()

