"""WebSocket server for real-time dashboard monitoring."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    """Manages WebSocket connections and broadcasts."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.metrics_buffer: list[dict] = []
        self.max_buffer = 1000

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)

    async def broadcast_metric(self, metric_type: str, data: dict):
        message = {
            "type": "metric",
            "metric_type": metric_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }
        self.metrics_buffer.append(message)
        if len(self.metrics_buffer) > self.max_buffer:
            self.metrics_buffer = self.metrics_buffer[-self.max_buffer:]
        await self.broadcast(message)

    async def broadcast_alert(self, severity: str, title: str, message: str, data: dict | None = None):
        alert = {
            "type": "alert",
            "severity": severity,
            "title": title,
            "message": message,
            "data": data or {},
            "timestamp": datetime.now().isoformat(),
        }
        await self.broadcast(alert)

    async def broadcast_pipeline_status(self, pipeline_id: str, status: str, phase: str = "", progress: float = 0.0, features_used: list[str] | None = None):
        await self.broadcast({
            "type": "pipeline_status",
            "pipeline_id": pipeline_id,
            "status": status,
            "phase": phase,
            "progress": progress,
            "features_used": features_used or [],
            "timestamp": datetime.now().isoformat(),
        })

    def get_metrics_buffer(self, limit: int = 100) -> list[dict]:
        return self.metrics_buffer[-limit:]

    def get_connection_count(self) -> int:
        return len(self.active_connections)


# Global instance
_manager: ConnectionManager | None = None

def get_ws_manager() -> ConnectionManager:
    global _manager
    if _manager is None:
        _manager = ConnectionManager()
    return _manager


# WebSocket routes (to be added to FastAPI app)
async def websocket_endpoint(websocket: WebSocket):
    manager = get_ws_manager()
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle client messages (subscribe to specific metrics, etc.)
            msg = json.loads(data) if data else {}
            if msg.get("type") == "ping":
                await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})
            elif msg.get("type") == "get_metrics":
                metrics = manager.get_metrics_buffer(msg.get("limit", 100))
                await websocket.send_json({"type": "metrics_buffer", "data": metrics})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
