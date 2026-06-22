"""Base agent class with dependency injection support."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from Database.connection import async_session_factory


class AgentContext:
    """Context passed to every agent during execution."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session


class BaseAgent(ABC):
    """Abstract base agent with DI support."""

    def __init__(self, name: str = "") -> None:
        self.name = name or self.__class__.__name__

    async def __call__(self, **kwargs: Any) -> Any:
        async with async_session_factory() as session:
            ctx = AgentContext(session=session)
            try:
                return await self.execute(ctx, **kwargs)
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    @abstractmethod
    async def execute(self, ctx: AgentContext, **kwargs: Any) -> Any:
        """Execute the agent's task."""
        ...
