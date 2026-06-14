"""Test configuration — use SQLite to avoid needing PostgreSQL."""

from __future__ import annotations

import os

# Set database to SQLite before any imports
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

# Initialize database tables at import time
from Database.connection import engine, Base
import asyncio


def _init_sync():
    """Create tables synchronously at import time."""
    loop = asyncio.new_event_loop()
    try:
        async def init():
            from Database.connection import init_db
            await init_db()
        loop.run_until_complete(init())
    finally:
        loop.close()


_init_sync()
