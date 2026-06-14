"""Health check tool."""

from __future__ import annotations

import time
from MCP.schemas import HealthOutput

_start_time = time.time()


async def health() -> HealthOutput:
    """Return system health status."""
    return HealthOutput(
        status="ok",
        version="0.1.0",
        uptime_seconds=time.time() - _start_time,
    )
