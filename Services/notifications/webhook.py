from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import hashlib


class WebhookConfig(BaseModel):
    webhook_id: str = ""
    name: str
    url: str
    platform: str = "discord"  # discord/slack/telegram/custom
    events: list[str] = []  # campaign.created, viral.detected, crisis.detected
    enabled: bool = True
    created_at: str = ""


class AlertPayload(BaseModel):
    event_type: str
    title: str
    message: str
    data: dict = {}
    severity: str = "info"  # info/warning/critical
    timestamp: str = ""


class WebhookManager:
    def __init__(self):
        self.webhooks: dict[str, WebhookConfig] = {}
        self.sent_alerts: list[dict] = []

    async def register_webhook(self, name, url, platform="discord", events=None) -> WebhookConfig:
        webhook_id = hashlib.md5(f"{name}:{url}".encode()).hexdigest()[:10]
        config = WebhookConfig(webhook_id=webhook_id, name=name, url=url, platform=platform, events=events or [], created_at=datetime.now().isoformat())
        self.webhooks[webhook_id] = config
        return config

    async def send_alert(self, event_type, title, message, data=None, severity="info") -> dict:
        payload = AlertPayload(event_type=event_type, title=title, message=message, data=data or {}, severity=severity, timestamp=datetime.now().isoformat())
        matching = [w for w in self.webhooks.values() if w.enabled and (not w.events or event_type in w.events)]
        results = []
        for wh in matching:
            results.append({"webhook_id": wh.webhook_id, "platform": wh.platform, "status": "sent", "url": wh.url[:50] + "..."})
        self.sent_alerts.append({"event": event_type, "title": title, "matching_webhooks": len(results), "timestamp": payload.timestamp})
        return {"sent_to": len(results), "results": results, "payload": payload.model_dump()}

    async def list_webhooks(self) -> list[WebhookConfig]:
        return list(self.webhooks.values())

    async def delete_webhook(self, webhook_id: str) -> bool:
        if webhook_id in self.webhooks:
            del self.webhooks[webhook_id]
            return True
        return False

    async def get_alert_history(self, limit: int = 20) -> list[dict]:
        return self.sent_alerts[-limit:]
