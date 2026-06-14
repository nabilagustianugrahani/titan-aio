"""
TITAN AIO — MCP Standalone Server

Run as a Claude Code subprocess:

    claude mcp add titan-aio \\
        -e DATABASE_URL="sqlite+aiosqlite:////abs/path/to/data/titan.db" \\
        -- python /path/to/MCP/standalone.py

Or from .env:

    claude mcp add titan-aio --env-file /path/to/.env -- python /path/to/MCP/standalone.py

MCP protocol uses stdin/stdout for JSON-RPC.
NO non-JSON output may go to stdout — all logging → stderr.
"""

# ── Environment setup: MUST run before any project import ───────
import logging
import os
import sys
from pathlib import Path

# Remove DEBUG so engine doesn't echo SQL to stdout
os.environ.pop("DEBUG", None)

# Silence everything at the Python level before any logger is configured
logging.basicConfig(level=logging.CRITICAL, stream=sys.stderr, force=True)

# ── Path setup ───────────────────────────────────────────────────
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

(_project_root / "data").mkdir(parents=True, exist_ok=True)

if "DATABASE_URL" not in os.environ:
    _db = _project_root / "data" / "titan.db"
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:////{_db.as_posix().removeprefix('/')}"

# ── Silence all noisy loggers (post-hoc, after engines exist) ───
_silent = (
    "sqlalchemy", "httpx", "urllib3", "chromadb", "notion_client",
    "PIL", "asyncio", "aiosqlite", "alembic",
)
for name in _silent:
    l = logging.getLogger(name)
    l.handlers.clear()
    l.setLevel(logging.CRITICAL)
    l.propagate = False
    l.addHandler(logging.NullHandler())

# ── Import project modules ───────────────────────────────────────
import asyncio

# Import ALL models so metadata registers all tables
from Database.models import (  # noqa: E402
    Product, Review, Campaign, AvatarProfile,
    WinningHook, Metric, KnowledgeEntry,
)
from Database.connection import init_db  # noqa: E402

# Disable engine echo at the SQLAlchemy level directly
import Database.connection as db_conn
try:
    db_conn.engine.sync_engine._echo = False
except Exception:
    pass

asyncio.run(init_db())

from MCP.server import mcp  # noqa: E402

if __name__ == "__main__":
    mcp.run(transport="stdio")
