"""Health check tool with real system probing."""

from __future__ import annotations

import os
import shutil
import time

from MCP.schemas import HealthOutput
from Services.memory.vector_store import VectorStore

_start_time = time.time()
_vs = VectorStore()


async def _check_db() -> str:
    """Ping the database."""
    try:
        from sqlalchemy import text

        from Database.connection import async_session_factory

        async with async_session_factory() as s:
            await s.execute(text("SELECT 1"))
        return "ok"
    except Exception as exc:
        return f"error: {exc}"


async def health() -> HealthOutput:
    """Return system health status with real probes."""
    # Disk usage
    disk = shutil.disk_usage("/home")
    disk_free_mb = round(disk.free / (1024 * 1024), 1)
    disk_used_mb = round(disk.used / (1024 * 1024), 1)

    # ChromaDB
    chroma_status = "ok" if _vs.is_chroma_available() else "fallback (in-memory)"

    # DB ping
    db_status = await _check_db()

    # Service status
    services = {
        "chromadb": chroma_status,
        "vector_collections": _vs.collection_exists("winning_hooks") or 0,
    }
    if _vs.is_chroma_available():
        try:
            services["chroma_persist_dir"] = os.environ.get(
                "CHROMA_PERSIST_DIR", str(__import__("titan.config", fromlist=["settings"]).settings.CHROMA_PERSIST_DIR),  # type: ignore
            )
        except Exception:
            pass

    # Overall status
    overall = "ok"
    if db_status != "ok":
        overall = "degraded"

    return HealthOutput(
        status=overall,
        version="0.1.0",
        uptime_seconds=round(time.time() - _start_time, 1),
        database=db_status,
        chroma=chroma_status,
        disk_free_mb=disk_free_mb,
        disk_used_mb=disk_used_mb,
        services=services,
    )
