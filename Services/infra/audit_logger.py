"""In-memory audit logger for tracking system actions and events."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AuditEntry(BaseModel):
    entry_id: str = ""
    action: str
    actor: str = "system"
    target: str = ""
    details: dict = {}
    timestamp: str = ""


class AuditLogger:
    """Lightweight in-memory audit log.  Retains all entries for the process lifetime."""

    def __init__(self) -> None:
        self.entries: list[AuditEntry] = []
        self._counter: int = 0

    async def log(
        self,
        action: str,
        actor: str = "system",
        target: str = "",
        details: dict | None = None,
    ) -> AuditEntry:
        self._counter += 1
        entry = AuditEntry(
            entry_id=f"AUD-{self._counter:06d}",
            action=action,
            actor=actor,
            target=target,
            details=details or {},
            timestamp=datetime.now().isoformat(),
        )
        self.entries.append(entry)
        return entry

    async def query(
        self,
        action: str = "",
        actor: str = "",
        limit: int = 50,
    ) -> list[AuditEntry]:
        results = self.entries
        if action:
            results = [e for e in results if e.action == action]
        if actor:
            results = [e for e in results if e.actor == actor]
        return results[-limit:]

    async def get_stats(self) -> dict:
        actions: dict[str, int] = {}
        actors: dict[str, int] = {}
        for e in self.entries:
            actions[e.action] = actions.get(e.action, 0) + 1
            actors[e.actor] = actors.get(e.actor, 0) + 1
        return {
            "total_entries": len(self.entries),
            "by_action": actions,
            "by_actor": actors,
        }
