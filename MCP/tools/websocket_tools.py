"""MCP tools module."""

from __future__ import annotations

from MCP.instance import mcp


@mcp.tool()
async def ws_broadcast_metric(metric_type: str, data: str) -> dict:
    """Broadcast a metric update to all connected WebSocket clients."""
    from titan.websocket_server import get_ws_manager
    manager = get_ws_manager()
    d = json.loads(data) if isinstance(data, str) else {}
    await manager.broadcast_metric(metric_type=metric_type, data=d)
    return {"broadcast": True, "connections": manager.get_connection_count()}


@mcp.tool()
async def ws_broadcast_alert(severity: str, title: str, message: str) -> dict:
    """Broadcast an alert to all connected WebSocket clients."""
    from titan.websocket_server import get_ws_manager
    manager = get_ws_manager()
    await manager.broadcast_alert(severity=severity, title=title, message=message)
    return {"broadcast": True, "connections": manager.get_connection_count()}


@mcp.tool()
async def ws_broadcast_pipeline(pipeline_id: str, status: str, phase: str = "", progress: float = 0.0) -> dict:
    """Broadcast pipeline status update to all connected WebSocket clients."""
    from titan.websocket_server import get_ws_manager
    manager = get_ws_manager()
    await manager.broadcast_pipeline_status(pipeline_id=pipeline_id, status=status, phase=phase, progress=progress)
    return {"broadcast": True, "connections": manager.get_connection_count()}


@mcp.tool()
async def ws_get_connections() -> dict:
    """Get current WebSocket connection count and recent metrics."""
    from titan.websocket_server import get_ws_manager
    manager = get_ws_manager()
    return {
        "connections": manager.get_connection_count(),
        "buffer_size": len(manager.metrics_buffer),
    }
