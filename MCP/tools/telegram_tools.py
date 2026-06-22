from MCP.server import mcp

_bot = None

def _get_bot():
    global _bot
    if _bot is None:
        from Services.notifications.telegram_bot import TelegramBot
        _bot = TelegramBot()
    return _bot


@mcp.tool()
async def configure_telegram_bot(bot_token: str, chat_ids: str = "") -> dict:
    """Configure Telegram bot token and chat IDs for notifications."""
    bot = _get_bot()
    ids = [c.strip() for c in chat_ids.split(",") if c.strip()] if chat_ids else []
    config = await bot.configure(bot_token=bot_token, chat_ids=ids)
    return config.model_dump()


@mcp.tool()
async def send_telegram_notification(title: str, message: str, severity: str = "info") -> dict:
    """Send a notification to all configured Telegram chats."""
    bot = _get_bot()
    results = await bot.send_notification(title=title, message=message, severity=severity)
    return {"sent": len(results), "messages": [m.model_dump() for m in results]}


@mcp.tool()
async def handle_telegram_command(command: str, chat_id: str = "default", args: str = "") -> dict:
    """Handle a Telegram bot command."""
    bot = _get_bot()
    response = await bot.handle_command(command=command, chat_id=chat_id, args=args)
    return {"command": command, "response": response}


@mcp.tool()
async def get_telegram_stats() -> dict:
    """Get Telegram bot statistics."""
    bot = _get_bot()
    return await bot.get_stats()


@mcp.tool()
async def get_telegram_message_history(limit: int = 20) -> list[dict]:
    """Get recent Telegram message history."""
    bot = _get_bot()
    msgs = await bot.get_message_history(limit=limit)
    return [m.model_dump() for m in msgs]


@mcp.tool()
async def telegram_status() -> dict:
    """Get system status via Telegram format."""
    bot = _get_bot()
    response = await bot.handle_status_command()
    return {"response": response}


@mcp.tool()
async def telegram_revenue() -> dict:
    """Get today's revenue via Telegram format."""
    bot = _get_bot()
    response = await bot.handle_revenue_command()
    return {"response": response}


@mcp.tool()
async def telegram_report() -> dict:
    """Get weekly report via Telegram format."""
    bot = _get_bot()
    response = await bot.handle_report_command()
    return {"response": response}
