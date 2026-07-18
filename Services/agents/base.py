"""Base agent class with dependency injection + MessageBus support."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from sqlalchemy.ext.asyncio import AsyncSession

from Database.connection import async_session_factory

if TYPE_CHECKING:
    from Services.agents.message_bus import MessageBus


class AgentContext:
    """Context passed to every agent during execution.

    Provides session, shared state, and MessageBus for agent communication.
    """

    def __init__(
        self,
        session: AsyncSession,
        state: Any = None,
        bus: MessageBus | None = None,
    ) -> None:
        self.session = session
        self.state = state  # SharedState for pipeline execution
        self.bus = bus  # MessageBus for inter-agent communication


class BaseAgent(ABC):
    """Abstract base agent with DI + MessageBus support.

    Agents can communicate via the bus:
        ctx.bus.publish("event.type", {"key": "val"}, source=self.name)
        data = ctx.bus.get_latest("event.type")
    """

    def __init__(self, name: str = "") -> None:
        self.name = name or self.__class__.__name__

    async def __call__(
        self,
        state: Any = None,
        bus: MessageBus | None = None,
        **kwargs: Any,
    ) -> Any:
        """Execute agent with optional shared state and MessageBus.

        Args:
            state: Optional SharedState for reading/writing pipeline data
            bus: Optional MessageBus for inter-agent communication
            **kwargs: Agent-specific arguments

        Returns:
            Agent execution result

        """
        async with async_session_factory() as session:
            ctx = AgentContext(session=session, state=state, bus=bus)
            try:
                return await self.execute(ctx, **kwargs)
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    def publish(self, ctx: AgentContext, event_type: str, data: dict) -> str | None:
        """Publish an event to the MessageBus. No-op if bus is None."""
        if ctx.bus:
            return ctx.bus.publish(event_type, data, source=self.name)
        return None

    def subscribe(self, ctx: AgentContext, event_type: str) -> None:
        """Subscribe to an event type on the MessageBus.

        Override _on_event() to handle incoming events.
        Subscribed handler is auto-unregistered on AttributeError or TypeError.
        """
        if ctx.bus:
            ctx.bus.subscribe(event_type, self._on_event)

    def _on_event(self, event: dict) -> None:
        """Default event handler — override in subclass for reactive agents."""
        pass

    @abstractmethod
    async def execute(self, ctx: AgentContext, **kwargs: Any) -> Any:
        """Execute the agent's task."""
        ...
