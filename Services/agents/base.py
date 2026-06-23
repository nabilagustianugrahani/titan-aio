"""Base agent class with dependency injection support."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from Database.connection import async_session_factory


class AgentContext:
    """Context passed to every agent during execution."""

    def __init__(self, session: AsyncSession, state: Any = None) -> None:
        self.session = session
        self.state = state


class BaseAgent(ABC):
    """Abstract base agent with DI support."""

    def __init__(self, name: str = "") -> None:
        self.name = name or self.__class__.__name__

    async def __call__(self, state: Any = None, **kwargs: Any) -> Any:
        """Execute agent with optional shared state.

        Args:
            state: Optional SharedState for reading/writing pipeline data
            **kwargs: Agent-specific arguments

        Returns:
            Agent execution result
        """
        async with async_session_factory() as session:
            ctx = AgentContext(session=session, state=state)
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
