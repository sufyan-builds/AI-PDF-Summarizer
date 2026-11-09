"""Centralized configuration for SmartPDF AI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    """Application-wide configuration values."""

    app_name: str = "SmartPDF AI"
    version: str = "1.0.0"
    groq_model: str = "llama-3.3-70b-versatile"
    temperature: float = 0.3
    max_tokens: int = 1000
    request_timeout: int = 45
    output_dir: Path = Path("outputs")
    logs_dir: Path = Path("logs")


CONFIG = AppConfig()


SUMMARY_TYPES: tuple[str, ...] = (
    "executive",
    "detailed",
    "bullet",
)


def ensure_project_directories() -> None:
    """Create required runtime directories if they do not exist."""
    CONFIG.output_dir.mkdir(parents=True, exist_ok=True)
    CONFIG.logs_dir.mkdir(parents=True, exist_ok=True)

