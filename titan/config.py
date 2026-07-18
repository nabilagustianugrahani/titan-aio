"""Application configuration via pydantic-settings."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve project root from this file's location: titan/config.py -> project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    APP_NAME: str = "TITAN AIO"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:////" + (PROJECT_ROOT / "data" / "titan.db").as_posix().removeprefix("/")

    # S3 / Storage
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET: str = "titan-assets"
    S3_REGION: str = "auto"

    # ChromaDB
    CHROMA_PERSIST_DIR: str = str(PROJECT_ROOT / "data" / "chroma")

    # Google Drive
    GDRIVE_CREDENTIALS_FILE: str = str(PROJECT_ROOT / "credentials" / "gdrive.json")
    GDRIVE_FOLDER_ID: str = ""

    # Server — PORT from env (HF Space sets PORT=7860)
    HOST: str = "0.0.0.0"
    PORT: int = int(os.environ.get("PORT", 8080))

    # Generation Models
    IMAGE_MODEL: str = "black-forest-labs/FLUX.1-schnell"
    VIDEO_MODEL: str = "wan2.7-i2v"  # DashScope Wan 2.7 I2V (cloud, no GPU)

    # LoRA Policy
    LORA_MIN_USAGE: int = 20

    # HuggingFace
    HF_TOKEN: str = ""

    # ScrapingBee (headless browser proxy)
    SCRAPINGBEE_API_KEY: str = ""

    # TikTok API (Production)
    TIKTOK_CLIENT_KEY: str = ""
    TIKTOK_CLIENT_SECRET: str = ""

    # TikTok API (Sandbox)
    TIKTOK_SANDBOX_CLIENT_KEY: str = ""
    TIKTOK_SANDBOX_CLIENT_SECRET: str = ""

    # Zernio — Social Media API (14+ platforms)
    ZERNIO_API_KEY: str = ""        # Key 1: Instagram, YouTube
    ZERNIO_API_KEY_OLD: str = ""    # Key 2: TikTok, Facebook

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    TELEGRAM_WEBHOOK_SECRET: str = ""

    # Zernio webhook secret (for HMAC verification)
    ZERNIO_WEBHOOK_SECRET: str = ""

    def zernio_api_key_for(self, platform: str = "") -> str:
        """Return the right Zernio API key for a given platform.

        Key 1 → Instagram, YouTube
        Key 2 → TikTok, Facebook
        Fallback: whichever is set.
        """
        platform = platform.lower().strip()
        if platform in ("instagram", "youtube"):
            return self.ZERNIO_API_KEY or self.ZERNIO_API_KEY_OLD or ""
        if platform in ("tiktok", "facebook"):
            return self.ZERNIO_API_KEY_OLD or self.ZERNIO_API_KEY or ""
        # Default / unknown platform: try key 1 first, then key 2
        return self.ZERNIO_API_KEY or self.ZERNIO_API_KEY_OLD or ""

    # Telegram Bot (removed)


    # Success Thresholds
    GROWTH_SCALE_ROI: float = 2.0
    GROWTH_KILL_ROI: float = 0.5
    GROWTH_KILL_CONSECUTIVE: int = 2


    # Notion
    NOTION_TOKEN: str = ""
    NOTION_CAMPAIGN_DB: str = ""
    NOTION_KNOWLEDGE_DB: str = ""
    NOTION_TASKS_DB: str = ""

    # MongoDB Atlas
    MONGODB_URI: str = ""
    MONGODB_DB_NAME: str = "titan_aio"
    MONGODB_PUBLIC_KEY: str = ""
    MONGODB_PRIVATE_KEY: str = ""
    MONGODB_PROJECT_ID: str = ""
    MONGODB_CLIENT_ID: str = ""
    MONGODB_CLIENT_SECRET: str = ""

    # Timezone — VPS is IST (UTC+5:30), user is WIB (UTC+7)
    # All timestamps stored in UTC, displayed in user's timezone
    VPS_TIMEZONE: str = "Asia/Kolkata"  # VPS timezone
    USER_TIMEZONE: str = "Asia/Jakarta"  # User timezone (WIB, UTC+7)

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def resolve_database_url(cls, v: str) -> str:
        """Resolve relative SQLite paths to absolute from PROJECT_ROOT.
        Also ensures PostgreSQL URLs use asyncpg driver prefix."""
        if not isinstance(v, str):
            return v
        # PostgreSQL: ensure asyncpg driver prefix
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        # SQLite relative path resolution
        if v.startswith("sqlite"):
            idx = v.find(":///")
            if idx != -1:
                rel = v[idx + 4 :]  # path after ":///"
                if rel.startswith("."):
                    resolved = (PROJECT_ROOT / rel).resolve()
                    return v[: idx + 4] + str(resolved).lstrip("/")
        return v


settings = Settings()
