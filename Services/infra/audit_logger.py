"""Audit logger — persists to DB via AuditLogEntry model, with in-memory cache."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from Database.connection import async_session_factory
from Database.repository import Repository


class AuditEntry(BaseModel):
    entry_id: str = ""
    action: str
    actor: str = "system"
    target: str = ""
    details: dict = {}
    timestamp: str = ""


class AuditLogger:
    """Audit logger backed by the DB audit_log table.

    Stores all entries in the database so they survive restarts.
    Also maintains an in-memory hot cache for the last N entries.
    """

    def __init__(self, hot_cache_size: int = 200) -> None:
        self._hot: list[AuditEntry] = []
        self._hot_size = hot_cache_size

    async def log(
        self,
        action: str,
        actor: str = "system",
        target: str = "",
        details: dict | None = None,
    ) -> AuditEntry:
        """Persist an audit entry to the database and hot cache."""
        from Database.models import AuditLogEntry

        entry_data = {
            "action": action,
            "actor": actor,
            "target": target,
            "details": details or {},
        }

        try:
            async with async_session_factory() as session:
                repo: Repository = Repository(session, AuditLogEntry)
                created = await repo.create(**entry_data)
                entry_id = f"AUD-{created.id}"
        except Exception:
            entry_id = "memory"

        entry = AuditEntry(
            entry_id=entry_id,
            action=action,
            actor=actor,
            target=target,
            details=details or {},
            timestamp=datetime.now().isoformat(),
        )

        self._hot.append(entry)
        if len(self._hot) > self._hot_size:
            self._hot = self._hot[-self._hot_size:]

        return entry

    async def query(
        self,
        action: str = "",
        actor: str = "",
        limit: int = 50,
    ) -> list[AuditEntry]:
        """Query audit log — hot cache first, then DB."""
        # If only recent history needed, use hot cache
        if limit <= self._hot_size and not action and not actor:
            return self._hot[-limit:]

        # For filtered queries, combine hot + DB
        results: list[AuditEntry] = list(self._hot)

        try:
            from Database.models import AuditLogEntry

            async with async_session_factory() as session:
                repo: Repository = Repository(session, AuditLogEntry)
                filters = {}
                if action:
                    filters["action"] = action
                if actor:
                    filters["actor"] = actor
                if filters:
                    db_entries = await repo.find(**filters)
                else:
                    db_entries = await repo.list_all(limit=limit)
                for e in db_entries:
                    results.append(
                        AuditEntry(
                            entry_id=e.id,
                            action=e.action,
                            actor=e.actor,
                            target=e.target or "",
                            details=e.details or {},
                            timestamp=e.created_at.isoformat() if hasattr(e, "created_at") and e.created_at else "",
                        ),
                    )
        except Exception:
            pass  # fall back to hot cache only

        # De-dupe by entry_id (hot cache may overlap with DB)
        seen: set[str] = set()
        deduped = []
        for e in reversed(results):
            if e.entry_id not in seen:
                seen.add(e.entry_id)
                deduped.append(e)
        deduped.reverse()

        if action:
            deduped = [e for e in deduped if e.action == action]
        if actor:
            deduped = [e for e in deduped if e.actor == actor]

        return deduped[-limit:]

    async def get_stats(self) -> dict:
        """Get audit statistics."""
        actions: dict[str, int] = {}
        actors: dict[str, int] = {}

        for e in self._hot:
            actions[e.action] = actions.get(e.action, 0) + 1
            actors[e.actor] = actors.get(e.actor, 0) + 1

        # Try to get total from DB
        total = len(self._hot)
        try:
            from sqlalchemy import func, select

            from Database.models import AuditLogEntry

            async with async_session_factory() as session:
                result = await session.execute(select(func.count(AuditLogEntry.id)))
                total = result.scalar() or len(self._hot)
        except Exception:
            pass

        return {
            "total_entries": total,
            "hot_cache_entries": len(self._hot),
            "by_action": actions,
            "by_actor": actors,
        }
