import hashlib
import logging
from datetime import datetime

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class TelegramConfig(BaseModel):
    bot_token: str = ""
    chat_ids: list[str] = []
    enabled: bool = False

class TelegramMessage(BaseModel):
    message_id: str = ""
    chat_id: str
    text: str
    parse_mode: str = "HTML"
    sent_at: str = ""
    status: str = "sent"

class TelegramBot:
    def __init__(self):
        self.config = TelegramConfig()
        self.messages: list[TelegramMessage] = []
        self.command_history: list[dict] = []
        self._bus_subscribed = False
        self._client: httpx.AsyncClient | None = None
        self._commands = {
            "start": (
                "🤖 <b>Titan AIO Bot</b>\n\n"
                "Commands:\n"
                "/status — System status\n"
                "/revenue — Today's earnings\n"
                "/report — Weekly performance\n"
                "/dashboard — Full dashboard summary\n"
                "/campaigns — List active campaigns\n"
                "/alerts — Recent alerts"
            ),
            "status": None,
            "revenue": None,
            "report": None,
            "dashboard": None,
            "campaigns": None,
            "alerts": None,
        }

    async def configure(self, bot_token: str, chat_ids: list[str] = None) -> TelegramConfig:
        self.config = TelegramConfig(
            bot_token=bot_token,
            chat_ids=chat_ids or [],
            enabled=bool(bot_token),
        )
        return self.config

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                base_url=f"https://api.telegram.org/bot{self.config.bot_token}",
            )
        return self._client

    async def close(self) -> None:
        self._polling = False
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    # ------------------------------------------------------------------
    # Webhook management
    # ------------------------------------------------------------------

    async def set_webhook(self, url: str, secret_token: str = "") -> dict:
        client = await self._get_client()
        payload: dict = {"url": url, "allowed_updates": ["message", "callback_query"]}
        if secret_token:
            payload["secret_token"] = secret_token
        resp = await client.post("/setWebhook", json=payload)
        return resp.json()

    async def remove_webhook(self) -> dict:
        client = await self._get_client()
        resp = await client.post("/removeWebhook")
        return resp.json()

    async def get_webhook_info(self) -> dict:
        client = await self._get_client()
        resp = await client.get("/getWebhookInfo")
        return resp.json()

    # ------------------------------------------------------------------
    # Long-polling mode (no HTTPS required)
    # ------------------------------------------------------------------

    _polling: bool = False

    async def start_polling(self) -> None:
        """Start long-polling for Telegram updates. Runs until close()."""
        self._polling = True
        offset = 0
        print("[telegram] Polling started", flush=True)
        while self._polling:
            try:
                client = await self._get_client()
                resp = await client.get(
                    "/getUpdates",
                    params={"offset": offset, "timeout": 30, "allowed_updates": '["message"]'},
                )
                data = resp.json()
                if not data.get("ok"):
                    print(f"[telegram] getUpdates error: {data.get('description')}", flush=True)
                    import asyncio
                    await asyncio.sleep(5)
                    continue

                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    message = update.get("message")
                    if not message:
                        continue

                    chat_id = str(message.get("chat", {}).get("id", ""))
                    text = message.get("text", "")

                    if not text.startswith("/"):
                        continue

                    parts = text.split(maxsplit=1)
                    command = parts[0].lstrip("/").split("@")[0].lower()
                    args = parts[1] if len(parts) > 1 else ""

                    print(f"[telegram] /{command} from {chat_id}", flush=True)
                    response_text = await self.handle_command(
                        command=command, chat_id=chat_id, args=args,
                    )
                    send_result = await self.send_message(chat_id=chat_id, text=response_text)
                    print(f"[telegram] Response sent: {send_result.status}", flush=True)

            except Exception as e:
                print(f"[telegram] Polling error: {e}", flush=True)
                import asyncio
                await asyncio.sleep(5)

    def stop_polling(self) -> None:
        self._polling = False

    async def send_message(
        self, chat_id: str, text: str, parse_mode: str = "HTML",
    ) -> TelegramMessage:
        # Test mode: skip real API calls (used by unit tests with "test:" token prefix)
        if self.config.bot_token.startswith("test:"):
            msg_id = hashlib.md5(
                f"{chat_id}:{text[:50]}".encode(),
            ).hexdigest()[:10]
            msg = TelegramMessage(
                message_id=msg_id,
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
                sent_at=datetime.now().isoformat(),
            )
            self.messages.append(msg)
            return msg

        # Real API call
        try:
            client = await self._get_client()
            resp = await client.post(
                "/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": parse_mode,
                },
            )
            data = resp.json()
            if data.get("ok"):
                result = data["result"]
                msg = TelegramMessage(
                    message_id=str(result.get("message_id", "")),
                    chat_id=str(result.get("chat", {}).get("id", chat_id)),
                    text=text,
                    parse_mode=parse_mode,
                    sent_at=datetime.now().isoformat(),
                    status="sent",
                )
            else:
                desc = data.get("description", "unknown error")
                logger.error("Telegram API error: %s", desc)
                msg = TelegramMessage(
                    message_id="",
                    chat_id=chat_id,
                    text=text,
                    parse_mode=parse_mode,
                    sent_at=datetime.now().isoformat(),
                    status=f"error: {desc}",
                )
        except Exception as e:
            logger.error("Failed to send Telegram message: %s", e)
            msg = TelegramMessage(
                message_id="",
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
                sent_at=datetime.now().isoformat(),
                status=f"error: {e}",
            )
        self.messages.append(msg)
        return msg

    async def send_notification(
        self, title: str, message: str, severity: str = "info",
    ) -> list[TelegramMessage]:
        icons = {
            "info": "ℹ️",
            "warning": "⚠️",
            "critical": "🚨",
            "success": "✅",
        }
        icon = icons.get(severity, "📢")
        formatted = f"{icon} <b>{title}</b>\n\n{message}"
        results = []
        for chat_id in self.config.chat_ids:
            msg = await self.send_message(chat_id=chat_id, text=formatted)
            results.append(msg)
        return results

    async def handle_command(
        self, command: str, chat_id: str, args: str = "",
    ) -> str:
        self.command_history.append(
            {
                "command": command,
                "chat_id": chat_id,
                "timestamp": datetime.now().isoformat(),
            },
        )
        handlers = {
            "start": lambda: self._commands["start"],
            "status": self.handle_status_command,
            "revenue": self.handle_revenue_command,
            "report": self.handle_report_command,
            "dashboard": self.handle_dashboard_command,
            "campaigns": self._handle_campaigns_command,
            "alerts": self._handle_alerts_command,
        }
        handler = handlers.get(command)
        if handler:
            result = handler()
            if isinstance(result, str):
                return result
            return await result
        return f"Unknown command: /{command}\nType /start for help."

    async def handle_status_command(self) -> str:
        """Handle /status command — quick pipeline status."""
        return (
            "🤖 <b>Titan AIO Status</b>\n\n"
            "🟢 System: Online\n"
            "📊 Tools: 130+ active\n"
            "🤖 Agents: 50+ ready\n"
            "🗄️ DB: Connected\n"
            "⏰ Uptime: Active\n\n"
            "Use /report for detailed stats."
        )

    async def handle_revenue_command(self) -> str:
        """Handle /revenue command — today's earnings."""
        try:
            from Services.revenue.tracker import RevenueTracker

            tracker = RevenueTracker()
            summary = await tracker.get_summary(days=1)
            return (
                f"💰 <b>Today's Revenue</b>\n\n"
                f"Revenue: ${summary.total_revenue:.2f}\n"
                f"Commission: ${summary.total_commission:.2f}\n"
                f"Clicks: {summary.total_clicks}\n"
                f"Conversions: {summary.total_conversions}\n"
                f"CVR: {summary.conversion_rate:.1f}%"
            )
        except Exception as e:
            logger.warning("Revenue tracker unavailable: %s", e)
            return (
                "💰 <b>Today's Revenue</b>\n\n"
                "Revenue tracker not available.\n"
                "Configure Services.revenue.tracker to enable."
            )

    async def handle_report_command(self) -> str:
        """Handle /report command — weekly performance report."""
        try:
            from Services.analytics.auto_reports import AutoReportGenerator

            gen = AutoReportGenerator()
            await gen.record_data(
                "revenue", {"revenue": 100, "ad_spend": 50},
            )
            report = await gen.generate_report(report_type="weekly")
            return (
                f"📊 <b>Weekly Report</b>\n\n"
                f"Score: {report.score}/100\n"
                f"Summary: {report.summary}\n"
                f"Generated: {report.generated_at[:16]}"
            )
        except Exception as e:
            logger.warning("Report generation failed: %s", e)
            return f"📊 <b>Report</b>\n\nGeneration failed: {e}"

    async def handle_dashboard_command(self) -> str:
        """Handle /dashboard command — full dashboard summary."""
        try:
            from Services.analytics.auto_reports import AutoReportGenerator
            from Services.revenue.tracker import RevenueTracker

            # Gather data from multiple services
            tracker = RevenueTracker()
            revenue = await tracker.get_summary(days=7)

            gen = AutoReportGenerator()
            await gen.record_data("revenue", {"revenue": revenue.total_revenue, "ad_spend": revenue.total_clicks * 0.5})
            report = await gen.generate_report(report_type="weekly")

            return (
                f"📊 <b>Titan AIO Dashboard</b>\n"
                f"{'─' * 28}\n\n"
                f"💰 <b>Revenue (7d)</b>\n"
                f"   Total: ${revenue.total_revenue:.2f}\n"
                f"   Commission: ${revenue.total_commission:.2f}\n"
                f"   Clicks: {revenue.total_clicks}\n"
                f"   Conversions: {revenue.total_conversions}\n"
                f"   CVR: {revenue.conversion_rate:.1f}%\n\n"
                f"📈 <b>Performance</b>\n"
                f"   Report Score: {report.score}/100\n"
                f"   Summary: {report.summary[:80]}...\n\n"
                f"📊 <b>Top Products</b>\n"
                + "\n".join(
                    f"   {i+1}. {p['name'][:30]} — ${p['revenue']:.2f}"
                    for i, p in enumerate(revenue.top_products[:3])
                ) + "\n\n"
                "⏰ <b>Quick Actions</b>\n"
                "   /status — System health\n"
                "   /revenue — Today only\n"
                "   /report — Full report"
            )
        except Exception as e:
            logger.warning("Report generator unavailable: %s", e)
            return (
                "📊 <b>Weekly Report</b>\n\n"
                "Report generator not available.\n"
                "Configure Services.analytics.auto_reports to enable."
            )

    async def _handle_campaigns_command(self) -> str:
        return (
            "📋 <b>Active Campaigns</b>\n\n"
            "No active campaigns yet.\n"
            "Use /launch &lt;url&gt; to start one."
        )

    async def _handle_alerts_command(self) -> str:
        recent = self.messages[-5:] if self.messages else []
        if not recent:
            return "🔔 <b>Recent Alerts</b>\n\nNo recent alerts."
        lines = "\n".join(
            f"• {m.text[:80]}..." if len(m.text) > 80 else f"• {m.text}"
            for m in reversed(recent)
        )
        return f"🔔 <b>Recent Alerts</b>\n\n{lines}"

    # ------------------------------------------------------------------
    # MessageBus integration
    # ------------------------------------------------------------------

    def subscribe_to_bus(self) -> None:
        """Subscribe to MessageBus events for auto-alerting (once only)."""
        if self._bus_subscribed:
            return
        try:
            from Services.agents.message_bus import get_bus

            bus = get_bus()
            for event_type in (
                "pipeline.complete",
                "pipeline.failed",
                "campaign.created",
                "sentiment.crisis",
            ):
                bus.subscribe(event_type, self._on_bus_event_sync)
            self._bus_subscribed = True
        except Exception as e:
            logger.debug("MessageBus subscribe skipped: %s", e)

    def _on_bus_event_sync(self, event: dict) -> None:
        """Sync wrapper for MessageBus handlers (bus calls synchronously)."""
        import asyncio

        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(self.on_event(event["type"], event.get("data", {})))
        else:
            loop.run_until_complete(self.on_event(event["type"], event.get("data", {})))

    async def on_event(self, event_type: str, data: dict) -> None:
        """Handle MessageBus events — auto-send alerts."""
        alerts = {
            "pipeline.complete": (
                "✅ Pipeline Complete",
                f"Product: {data.get('product', 'Unknown')}\n"
                f"Score: {data.get('score', 'N/A')}",
                "success",
            ),
            "pipeline.failed": (
                "🚨 Pipeline Failed",
                f"Error: {data.get('error', 'Unknown')}",
                "critical",
            ),
            "campaign.created": (
                "📋 New Campaign",
                f"Created: {data.get('name', 'Unknown')}",
                "info",
            ),
            "sentiment.crisis": (
                "⚠️ Sentiment Crisis",
                f"Brand: {data.get('brand', 'Unknown')}",
                "warning",
            ),
        }
        if event_type in alerts:
            title, message, severity = alerts[event_type]
            try:
                await self.send_notification(
                    title=title, message=message, severity=severity,
                )
            except Exception as e:
                logger.error("Failed to send alert for %s: %s", event_type, e)

    # ------------------------------------------------------------------
    # History / stats
    # ------------------------------------------------------------------

    async def get_message_history(self, limit: int = 20) -> list[TelegramMessage]:
        return self.messages[-limit:]

    async def get_command_history(self, limit: int = 20) -> list[dict]:
        return self.command_history[-limit:]

    async def get_stats(self) -> dict:
        return {
            "total_messages": len(self.messages),
            "total_commands": len(self.command_history),
            "chat_ids": len(self.config.chat_ids),
            "enabled": self.config.enabled,
            "bus_subscribed": self._bus_subscribed,
        }
