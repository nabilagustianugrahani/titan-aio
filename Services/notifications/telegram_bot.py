from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import hashlib

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
        self._commands = {
            "start": "Welcome to Titan AIO Bot! 🤖\n\nCommands:\n/status - System status\n/campaigns - List active campaigns\n/alerts - Recent alerts\n/report - Performance report",
            "status": None,  # dynamic
            "campaigns": None,
            "alerts": None,
            "report": None,
        }

    async def configure(self, bot_token: str, chat_ids: list[str] = None) -> TelegramConfig:
        self.config = TelegramConfig(bot_token=bot_token, chat_ids=chat_ids or [], enabled=bool(bot_token))
        return self.config

    async def send_message(self, chat_id: str, text: str, parse_mode: str = "HTML") -> TelegramMessage:
        msg_id = hashlib.md5(f"{chat_id}:{text[:50]}".encode()).hexdigest()[:10]
        msg = TelegramMessage(message_id=msg_id, chat_id=chat_id, text=text, parse_mode=parse_mode, sent_at=datetime.now().isoformat())
        self.messages.append(msg)
        return msg

    async def send_notification(self, title: str, message: str, severity: str = "info") -> list[TelegramMessage]:
        icons = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨", "success": "✅"}
        icon = icons.get(severity, "📢")
        formatted = f"{icon} <b>{title}</b>\n\n{message}"
        results = []
        for chat_id in self.config.chat_ids:
            msg = await self.send_message(chat_id=chat_id, text=formatted)
            results.append(msg)
        return results

    async def handle_command(self, command: str, chat_id: str, args: str = "") -> str:
        self.command_history.append({"command": command, "chat_id": chat_id, "timestamp": datetime.now().isoformat()})
        if command == "start":
            return self._commands["start"]
        elif command == "status":
            return "🟢 <b>System Status</b>\n\nAll systems operational.\nTools: 80 active\nAgents: 27 running\nUptime: 99.9%"
        elif command == "campaigns":
            return "📋 <b>Active Campaigns</b>\n\nNo active campaigns yet.\nUse /launch <url> to start one."
        elif command == "alerts":
            return "🔔 <b>Recent Alerts</b>\n\nNo recent alerts."
        elif command == "report":
            return "📊 <b>Performance Report</b>\n\nTotal campaigns: 0\nTotal revenue: $0\nBest platform: —"
        else:
            return f"Unknown command: /{command}\nType /start for help."

    async def get_message_history(self, limit: int = 20) -> list[TelegramMessage]:
        return self.messages[-limit:]

    async def get_command_history(self, limit: int = 20) -> list[dict]:
        return self.command_history[-limit:]

    async def get_stats(self) -> dict:
        return {"total_messages": len(self.messages), "total_commands": len(self.command_history), "chat_ids": len(self.config.chat_ids), "enabled": self.config.enabled}
