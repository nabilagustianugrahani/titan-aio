"""Generic async repository with CRUD operations."""

from __future__ import annotations

import uuid
from typing import Any, Generic, Optional, TypeVar

from sqlalchemy import Select, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from Database.connection import Base

ModelT = TypeVar("ModelT", bound=Base)


class Repository(Generic[ModelT]):
    """Generic async repository for SQLAlchemy models."""

    def __init__(self, session: AsyncSession, model: type[ModelT]) -> None:
        self._session = session
        self._model = model

    async def create(self, **kwargs: Any) -> ModelT:
        """Create a new record."""
        if "id" not in kwargs:
            kwargs["id"] = str(uuid.uuid4())
        instance = self._model(**kwargs)
        self._session.add(instance)
        await self._session.flush()
        return instance

    async def get(self, id: str) -> Optional[ModelT]:
        """Get a record by ID."""
        stmt = select(self._model).where(self._model.id == id)  # type: ignore[attr-defined]
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def find(self, **filters: Any) -> list[ModelT]:
        """Find records matching filters."""
        stmt = select(self._model)
        for key, value in filters.items():
            column = getattr(self._model, key, None)
            if column is not None:
                stmt = stmt.where(column == value)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, id: str, **kwargs: Any) -> Optional[ModelT]:
        """Update a record by ID."""
        stmt = (
            update(self._model)
            .where(self._model.id == id)  # type: ignore[attr-defined]
            .values(**kwargs)
            .returning(self._model)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.scalar_one_or_none()

    async def delete(self, id: str) -> bool:
        """Delete a record by ID. Returns True if deleted."""
        stmt = delete(self._model).where(self._model.id == id)  # type: ignore[attr-defined]
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount > 0

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[ModelT]:
        """List all records with pagination."""
        stmt = select(self._model).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
