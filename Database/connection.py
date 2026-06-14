"""Database connection and session management."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from titan.config import PROJECT_ROOT, settings

# Use extend_existing to allow model re-imports during testing
metadata = MetaData()


class Base(DeclarativeBase):
    metadata = metadata


# Ensure the database directory exists for file-based SQLite databases.
# This must happen before engine creation (which would fail if the
# directory does not exist).
_db_url: str = settings.DATABASE_URL
if _db_url.startswith("sqlite") and ":memory:" not in _db_url:
    # Extract path after "://". SQLite://path, sqlite+aiosqlite://path
    _auth_part = _db_url.split("://", 1)[1] if "://" in _db_url else _db_url
    # If auth part starts with /, it's absolute. Strip leading / for path
    _raw_path = _auth_part.lstrip("/")
    _path = Path(_raw_path)
    # If it was absolute (had leading /), restore it
    if _auth_part.startswith("/"):
        _path = Path("/" + _raw_path)
    _path.parent.mkdir(parents=True, exist_ok=True)

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=20,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session():  # type: ignore[misc]
    """Dependency that yields an async session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Create all tables. Safe to call on every startup (CREATE IF NOT EXISTS)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Dispose of the engine."""
    await engine.dispose()
