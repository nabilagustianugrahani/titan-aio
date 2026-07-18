"""MCP tools module."""

from __future__ import annotations

from MCP.instance import mcp

_logger = None


def _get_logger():
    global _logger
    if _logger is None:
        from Services.infra.audit_logger import AuditLogger

        _logger = AuditLogger()
    return _logger


@mcp.tool()
async def log_audit_event(
    action: str,
    actor: str = "system",
    target: str = "",
    details: str = "",
) -> dict:
    """Log an audit event for tracking."""
    logger = _get_logger()
    d = json.loads(details) if details else {}
    entry = await logger.log(action=action, actor=actor, target=target, details=d)
    return entry.model_dump()


@mcp.tool()
async def query_audit_log(
    action: str = "",
    actor: str = "",
    limit: int = 50,
) -> list[dict]:
    """Query audit log entries."""
    logger = _get_logger()
    entries = await logger.query(action=action, actor=actor, limit=limit)
    return [e.model_dump() for e in entries]


@mcp.tool()
async def get_audit_stats() -> dict:
    """Get audit log statistics."""
    logger = _get_logger()
    return await logger.get_stats()
