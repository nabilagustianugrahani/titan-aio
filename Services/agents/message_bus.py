"""Message Bus — inter-agent communication. Zero deps, in-memory.

Enhanced version with:
- Error handling per handler (not silent pass)
- Configurable max_history
- clear() method for testing
- Logger instead of print
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class MessageBus:
    """Lightweight event bus. Agents publish, others subscribe or poll."""

    def __init__(self, max_history: int = 1000):
        self._handlers: dict[str, list[Callable]] = {}
        self._latest: dict[str, dict] = {}
        self._history: list[dict] = []
        self._max_history = max_history

    def publish(self, event_type: str, data: dict, source: str = "") -> str:
        """Publish event with error handling."""
        eid = str(uuid.uuid4())
        event = {
            "id": eid,
            "type": event_type,
            "data": data,
            "source": source,
            "ts": datetime.utcnow().isoformat(),
        }
        self._latest[event_type] = event
        self._history.append(event)

        # Trim history
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history // 2:]

        # Notify handlers with error handling
        for handler in self._handlers.get(event_type, []):
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Handler error for {event_type}: {e}")

        return eid

    def subscribe(self, event_type: str, handler: Callable):
        """Subscribe to event type."""
        self._handlers.setdefault(event_type, []).append(handler)

    def unsubscribe(self, event_type: str, handler: Callable):
        """Unsubscribe from event type."""
        handlers = self._handlers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)

    def get_latest(self, event_type: str) -> Optional[dict]:
        """Get latest event data."""
        e = self._latest.get(event_type)
        return e["data"] if e else None

    def get_history(self, event_type: str = "", limit: int = 10) -> list[dict]:
        """Get event history."""
        events = [e for e in self._history if not event_type or e["type"] == event_type]
        return events[-limit:]

    def clear(self):
        """Clear all handlers and history."""
        self._handlers.clear()
        self._latest.clear()
        self._history.clear()


# ── Singleton ──────────────────────────────────────────────────────

_bus: MessageBus | None = None


def get_bus() -> MessageBus:
    global _bus
    if _bus is None:
        _bus = MessageBus()
    return _bus
