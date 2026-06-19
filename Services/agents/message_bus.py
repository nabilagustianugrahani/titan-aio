"""Message Bus — inter-agent communication. Zero deps, in-memory."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Callable


class MessageBus:
    """Lightweight event bus. Agents publish, others subscribe or poll."""

    def __init__(self):
        self._handlers: dict[str, list[Callable]] = {}
        self._latest: dict[str, dict] = {}
        self._history: list[dict] = []

    def publish(self, event_type: str, data: dict, source: str = "") -> str:
        eid = str(uuid.uuid4())
        event = {"id": eid, "type": event_type, "data": data, "source": source, "ts": datetime.utcnow().isoformat()}
        self._latest[event_type] = event
        self._history.append(event)
        if len(self._history) > 1000:
            self._history = self._history[-500:]
        for h in self._handlers.get(event_type, []):
            try: h(event)
            except Exception: pass
        return eid

    def subscribe(self, event_type: str, handler: Callable):
        self._handlers.setdefault(event_type, []).append(handler)

    def get_latest(self, event_type: str) -> dict | None:
        e = self._latest.get(event_type)
        return e["data"] if e else None

    def get_history(self, event_type: str = "", limit: int = 10) -> list[dict]:
        events = [e for e in self._history if not event_type or e["type"] == event_type]
        return events[-limit:]

_bus: MessageBus | None = None

def get_bus() -> MessageBus:
    global _bus
    if _bus is None: _bus = MessageBus()
    return _bus
