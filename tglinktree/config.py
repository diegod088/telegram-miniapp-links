"""Application configuration via Pydantic BaseSettings."""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache


class Settings(BaseSettings):
    """All configuration loaded from environment variables / .env file."""

    # ── Telegram ──────────────────────────────────────────────
    BOT_TOKEN: str
    BOT_USERNAME: str = ""
    WEBAPP_URL: str = "https://example.com"

    # ── Database ──────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/tglinktree"

    # ── Redis ─────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379"

    # ── Security ──────────────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production"
    INIT_DATA_EXPIRY_SECONDS: int = 86400  # 24 hours

    # ── Plan Limits ───────────────────────────────────────────
    MAX_LINKS_FREE: int = 5
    MAX_LINKS_PRO: int = 50
    MAX_LINKS_BUSINESS: int = 500

    # ── Feature Flags ─────────────────────────────────────────
    PAYMENTS_ENABLED: bool = False

    # ── Affiliate Tags ────────────────────────────────────────
    AFFILIATE_TAG_AMAZON: str = ""
    AFFILIATE_TAG_ALIEXPRESS: str = ""
    AFFILIATE_TAG_TEMU: str = ""
    AFFILIATE_TAG_SHEIN: str = ""
    AFFILIATE_TAG_TERABOX: str = ""
    AFFILIATE_TAG_STREAMTAPE: str = ""
    AFFILIATE_TAG_DOODSTREAM: str = ""
    AFFILIATE_TAG_VOE_SX: str = ""

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not (v.startswith("postgresql+asyncpg://") or v.startswith("sqlite+aiosqlite://")):
            raise ValueError(
                "DATABASE_URL must use 'postgresql+asyncpg://' or 'sqlite+aiosqlite://'"
            )
        return v

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
