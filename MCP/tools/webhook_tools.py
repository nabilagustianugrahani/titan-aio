"""MCP tools module."""

from __future__ import annotations

from MCP.instance import mcp

_manager = None


def _get_manager():
    global _manager
    if _manager is None:
        from Services.notifications.webhook import WebhookManager
        _manager = WebhookManager()
    return _manager


@mcp.tool()
async def register_webhook_alert(name: str, url: str, platform: str = "discord", events: str = "") -> dict:
    """Register a webhook for notifications (Discord/Slack/Telegram)."""
    mgr = _get_manager()
    result = await mgr.register_webhook(name=name, url=url, platform=platform, events=events.split(",") if events else [])
    return result.model_dump()


@mcp.tool()
async def send_webhook_alert(event_type: str, title: str, message: str, severity: str = "info") -> dict:
    """Send an alert to all matching webhooks."""
    mgr = _get_manager()
    return await mgr.send_alert(event_type=event_type, title=title, message=message, severity=severity)


@mcp.tool()
async def list_webhook_alerts() -> list[dict]:
    """List all registered webhooks."""
    mgr = _get_manager()
    return [w.model_dump() for w in await mgr.list_webhooks()]


@mcp.tool()
async def get_alert_history(limit: int = 20) -> list[dict]:
    """Get recent alert history."""
    mgr = _get_manager()
    return await mgr.get_alert_history(limit=limit)


@mcp.tool()
async def delete_webhook_alert(webhook_id: str) -> dict:
    """Delete a webhook."""
    mgr = _get_manager()
    success = await mgr.delete_webhook(webhook_id)
    return {"success": success}
