"""Application configuration via pydantic-settings."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


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
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/titan.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # S3 / Storage
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET: str = "titan-assets"
    S3_REGION: str = "auto"

    # ChromaDB
    CHROMA_PERSIST_DIR: str = str(Path.cwd() / "data" / "chroma")

    # Google Drive
    GDRIVE_CREDENTIALS_FILE: str = str(Path.cwd() / "credentials" / "gdrive.json")
    GDRIVE_FOLDER_ID: str = ""

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8080

    # Generation Models
    IMAGE_MODEL: str = "black-forest-labs/FLUX.1-schnell"
    VIDEO_MODEL: str = "Wan-AI/Wan2.2-T2V-14B"

    # LoRA Policy
    LORA_MIN_USAGE: int = 20

    # Success Thresholds
    GROWTH_SCALE_ROI: float = 2.0
    GROWTH_KILL_ROI: float = 0.5
    GROWTH_KILL_CONSECUTIVE: int = 2

    # Kaggle
    KAGGLE_USERNAME: str = ""
    KAGGLE_KEY: str = ""
    KAGGLE_NOTEBOOK_PATH: str = "kaggle-notebook-template.py"

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


settings = Settings()
