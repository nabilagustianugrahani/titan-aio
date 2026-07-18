"""Swarm config — adapted from MiroFish, reads Titan AIO env vars."""

from __future__ import annotations

import os


class Config:
    """Swarm module configuration.

    Reuses Titan AIO's env vars where possible:
    - OPENAI_API_KEY → LLM_API_KEY
    - ZEP_API_KEY (optional) — for GraphRAG
    """

    # LLM (reuses Titan AIO's OPENAI_API_KEY)
    LLM_API_KEY = os.environ.get("OPENAI_API_KEY") or os.environ.get("LLM_API_KEY")
    LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")
    LLM_MODEL_NAME = os.environ.get("LLM_MODEL_NAME", "gpt-4o-mini")

    # Zep (optional — enables GraphRAG)
    ZEP_API_KEY = os.environ.get("ZEP_API_KEY")

    # Upload paths
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "../uploads")

    # Text processing
    DEFAULT_CHUNK_SIZE = 500
    DEFAULT_CHUNK_OVERLAP = 50

    # Report Agent
    REPORT_AGENT_MAX_TOOL_CALLS = int(os.environ.get("REPORT_AGENT_MAX_TOOL_CALLS", "5"))
    REPORT_AGENT_MAX_REFLECTION_ROUNDS = int(os.environ.get("REPORT_AGENT_MAX_REFLECTION_ROUNDS", "2"))
    REPORT_AGENT_TEMPERATURE = float(os.environ.get("REPORT_AGENT_TEMPERATURE", "0.5"))

    @classmethod
    def validate(cls) -> list[str]:
        errors: list[str] = []
        if not cls.LLM_API_KEY:
            errors.append("LLM_API_KEY / OPENAI_API_KEY not configured")
        return errors
