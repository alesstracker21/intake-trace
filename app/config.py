from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env", override=False)


def _as_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().casefold() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_env: str = field(default_factory=lambda: os.getenv("APP_ENV", "local"))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    gemini_model: str = field(
        default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-3.7-flash")
    )
    gemini_review_model: str = field(
        default_factory=lambda: os.getenv(
            "GEMINI_REVIEW_MODEL", os.getenv("GEMINI_MODEL", "gemini-3.7-flash")
        )
    )
    output_dir: Path = field(
        default_factory=lambda: Path(os.getenv("OUTPUT_DIR", str(PROJECT_ROOT / "outputs")))
    )
    otel_enabled: bool = field(default_factory=lambda: _as_bool("OTEL_ENABLED"))
    otel_service_name: str = field(
        default_factory=lambda: os.getenv("OTEL_SERVICE_NAME", "intake-trace")
    )
    otel_endpoint: str = field(
        default_factory=lambda: os.getenv(
            "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "http://localhost:4318/v1/traces"
        )
    )


def get_settings() -> Settings:
    return Settings()
