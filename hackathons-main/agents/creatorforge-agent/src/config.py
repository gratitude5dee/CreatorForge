"""Runtime configuration for CreatorForge."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    db_path: str
    timezone: str
    log_level: str
    port: int

    openai_api_key: str
    openai_text_model: str
    openai_image_model: str

    nvm_api_key: str
    nvm_environment: str
    nvm_plan_id: str
    nvm_agent_id: str
    nvm_base_url: str

    mindra_api_url: str
    mindra_api_key: str
    mindra_timeout_seconds: int

    zeroclick_api_url: str
    zeroclick_api_key: str
    zeroclick_timeout_seconds: int

    budget_daily_cap: int
    budget_vendor_cap: int
    approval_threshold: int

    default_buyer_id: str


_REQUIRED_FIELDS = (
    "OPENAI_API_KEY",
    "NVM_API_KEY",
    "NVM_PLAN_ID",
    "NVM_AGENT_ID",
    "MINDRA_API_URL",
    "MINDRA_API_KEY",
    "ZEROCLICK_API_URL",
    "ZEROCLICK_API_KEY",
)


def _require(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def load_settings() -> Settings:
    """Load and validate runtime settings from environment."""
    for name in _REQUIRED_FIELDS:
        _require(name)

    return Settings(
        db_path=os.getenv("CREATORFORGE_DB_PATH", "./creatorforge.db"),
        timezone=os.getenv("CREATORFORGE_TIMEZONE", "America/Los_Angeles"),
        log_level=os.getenv("CREATORFORGE_LOG_LEVEL", "INFO"),
        port=int(os.getenv("PORT", "3010")),
        openai_api_key=_require("OPENAI_API_KEY"),
        openai_text_model=os.getenv("OPENAI_TEXT_MODEL", "gpt-4o"),
        openai_image_model=os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1"),
        nvm_api_key=_require("NVM_API_KEY"),
        nvm_environment=os.getenv("NVM_ENVIRONMENT", "sandbox"),
        nvm_plan_id=_require("NVM_PLAN_ID"),
        nvm_agent_id=_require("NVM_AGENT_ID"),
        nvm_base_url=os.getenv("NVM_BASE_URL", "http://localhost:3010"),
        mindra_api_url=_require("MINDRA_API_URL"),
        mindra_api_key=_require("MINDRA_API_KEY"),
        mindra_timeout_seconds=int(os.getenv("MINDRA_TIMEOUT_SECONDS", "30")),
        zeroclick_api_url=_require("ZEROCLICK_API_URL"),
        zeroclick_api_key=_require("ZEROCLICK_API_KEY"),
        zeroclick_timeout_seconds=int(os.getenv("ZEROCLICK_TIMEOUT_SECONDS", "20")),
        budget_daily_cap=int(os.getenv("BUDGET_DAILY_CAP", "50")),
        budget_vendor_cap=int(os.getenv("BUDGET_VENDOR_CAP", "20")),
        approval_threshold=int(os.getenv("APPROVAL_THRESHOLD", "10")),
        default_buyer_id=os.getenv("DEFAULT_BUYER_ID", "anonymous"),
    )
