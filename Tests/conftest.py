"""Test configuration — use SQLite to avoid needing PostgreSQL."""

from __future__ import annotations

import os
from pathlib import Path

# Set database to SQLite with absolute path
_TEST_DB = str(Path(__file__).resolve().parent.parent / "test.db")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:////{_TEST_DB.removeprefix('/')}"

# Import models so metadata registers all tables
import importlib, sys

# Ensure fresh reload
for mod in list(sys.modules.keys()):
    if "Database" in mod or "titan" in mod:
        del sys.modules[mod]

# Import ALL models so metadata registers every table before init_db
from Database.models import Product, Review, Campaign, AffiliateLink, GeneratedAsset
from Database.models import WinningHook, WinningProduct, WinningCTA, FailedCampaign
from Database.models import Metric, KnowledgeEntry, AvatarProfile, ProductProfile

# Now initialize the database (creates all registered tables)
from Database.connection import init_db
import asyncio

asyncio.run(init_db())

