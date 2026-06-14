"""Test configuration — use SQLite to avoid needing PostgreSQL."""

from __future__ import annotations

import os
from pathlib import Path

# Set database to SQLite with absolute path
_TEST_DB = str(Path(__file__).resolve().parent.parent / "test.db")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:////{_TEST_DB.lstrip('/')}"

# Import models so metadata registers all tables
import importlib, sys

# Ensure fresh reload
for mod in list(sys.modules.keys()):
    if "Database" in mod or "titan" in mod:
        del sys.modules[mod]

# Now import connection (will see our DATABASE_URL)
from Database.connection import init_db
import asyncio

asyncio.run(init_db())

