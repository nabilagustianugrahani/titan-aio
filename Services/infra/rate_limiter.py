from pydantic import BaseModel
from datetime import datetime, timedelta
import time


class RateLimitConfig(BaseModel):
    provider: str
    max_requests: int = 100
    window_seconds: int = 60
    current_count: int = 0
    window_start: str = ""


class APIRateLimiter:
    def __init__(self):
        self.limits: dict[str, RateLimitConfig] = {
            "gemini": RateLimitConfig(provider="gemini", max_requests=60, window_seconds=60),
            "openai": RateLimitConfig(provider="openai", max_requests=100, window_seconds=60),
            "flux": RateLimitConfig(provider="flux", max_requests=20, window_seconds=60),
            "wan": RateLimitConfig(provider="wan", max_requests=10, window_seconds=60),
            "shopee": RateLimitConfig(provider="shopee", max_requests=30, window_seconds=60),
            "tokopedia": RateLimitConfig(provider="tokopedia", max_requests=30, window_seconds=60),
            "notion": RateLimitConfig(provider="notion", max_requests=3, window_seconds=1),
        }
        self.request_log: list[dict] = []

    def can_request(self, provider: str) -> bool:
        config = self.limits.get(provider)
        if not config:
            return True
        now = time.time()
        window_start = float(config.window_start) if config.window_start else 0
        if now - window_start > config.window_seconds:
            config.current_count = 0
            config.window_start = str(now)
        return config.current_count < config.max_requests

    async def acquire(self, provider: str) -> dict:
        if not self.can_request(provider):
            config = self.limits.get(provider)
            wait_time = config.window_seconds - (time.time() - float(config.window_start or time.time()))
            return {"allowed": False, "provider": provider, "retry_after": max(1, int(wait_time)), "remaining": 0}
        config = self.limits.get(provider)
        if config:
            config.current_count += 1
            remaining = config.max_requests - config.current_count
        else:
            remaining = 999
        self.request_log.append({"provider": provider, "timestamp": datetime.now().isoformat()})
        return {"allowed": True, "provider": provider, "remaining": remaining}

    async def get_usage(self) -> dict:
        usage = {}
        for name, config in self.limits.items():
            usage[name] = {
                "max": config.max_requests,
                "current": config.current_count,
                "remaining": config.max_requests - config.current_count,
                "window": config.window_seconds,
            }
        return usage

    async def reset(self, provider: str = ""):
        if provider and provider in self.limits:
            self.limits[provider].current_count = 0
        else:
            for config in self.limits.values():
                config.current_count = 0

    async def get_stats(self) -> dict:
        return {
            "total_requests": len(self.request_log),
            "providers": await self.get_usage(),
        }
