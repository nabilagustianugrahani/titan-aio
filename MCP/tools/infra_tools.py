from MCP.server import mcp

_limiter = None
_cache = None


def _get_limiter():
    global _limiter
    if _limiter is None:
        from Services.infra.rate_limiter import APIRateLimiter
        _limiter = APIRateLimiter()
    return _limiter


def _get_cache():
    global _cache
    if _cache is None:
        from Services.infra.content_cache import ContentCache
        _cache = ContentCache()
    return _cache


@mcp.tool()
async def check_api_rate_limit(provider: str) -> dict:
    """Check if an API provider has available rate limit capacity."""
    limiter = _get_limiter()
    can = limiter.can_request(provider)
    usage = await limiter.get_usage()
    provider_usage = usage.get(provider, {})
    return {
        "provider": provider,
        "can_request": can,
        "remaining": provider_usage.get("remaining", 0),
        "max": provider_usage.get("max", 0),
    }


@mcp.tool()
async def acquire_api_slot(provider: str) -> dict:
    """Acquire a rate limit slot before making an API call. Returns retry_after if limited."""
    limiter = _get_limiter()
    return await limiter.acquire(provider=provider)


@mcp.tool()
async def get_api_rate_usage() -> dict:
    """Get rate limit usage for all providers."""
    limiter = _get_limiter()
    return await limiter.get_stats()


@mcp.tool()
async def reset_api_rate_limit(provider: str = "") -> dict:
    """Reset rate limit counters for a provider (or all)."""
    limiter = _get_limiter()
    await limiter.reset(provider=provider)
    return {"reset": True, "provider": provider or "all"}


@mcp.tool()
async def cache_get(content_type: str, key_params: str) -> dict | None:
    """Get cached content by type and key parameters."""
    cache = _get_cache()
    import json
    params = json.loads(key_params) if key_params else {}
    return await cache.get(content_type=content_type, params=params)


@mcp.tool()
async def cache_set(content_type: str, key_params: str, content: str) -> dict:
    """Store content in cache."""
    cache = _get_cache()
    import json
    params = json.loads(key_params) if key_params else {}
    content_dict = json.loads(content) if content else {}
    await cache.set(content_type=content_type, params=params, content=content_dict)
    return {"cached": True, "content_type": content_type}


@mcp.tool()
async def cache_stats() -> dict:
    """Get cache statistics."""
    cache = _get_cache()
    return await cache.get_stats()
