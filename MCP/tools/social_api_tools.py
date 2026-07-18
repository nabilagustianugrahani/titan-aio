"""MCP tools module."""

from __future__ import annotations

from MCP.instance import mcp

_tiktok = None
_aggregator = None


def _get_tiktok():  # type: ignore[no-untyped-def]
    global _tiktok
    if _tiktok is None:
        from Services.api.tiktok_client import TikTokClient
        from titan.config import settings

        _tiktok = TikTokClient(
            client_key=settings.TIKTOK_CLIENT_KEY,
            client_secret=settings.TIKTOK_CLIENT_SECRET,
            scrapingbee_key=settings.SCRAPINGBEE_API_KEY,
        )
    return _tiktok


def _get_aggregator():  # type: ignore[no-untyped-def]
    global _aggregator
    if _aggregator is None:
        from Services.api.social_aggregator import SocialAggregator

        _aggregator = SocialAggregator()
    return _aggregator


@mcp.tool()
async def tiktok_trending(category: str = "", limit: int = 20) -> list[dict]:
    """Get trending hashtags on TikTok.

    Args:
        category: Filter by category (e.g. 'fashion', 'beauty', 'education'). Empty = all.
        limit: Max results to return (default 20).

    """
    client = _get_tiktok()
    trends = await client.get_trending_hashtags(category=category, limit=limit)
    return [t.model_dump() for t in trends]


@mcp.tool()
async def tiktok_search(query: str, count: int = 20) -> list[dict]:
    """Search for videos on TikTok by keyword.

    Args:
        query: Search keyword (e.g. 'wireless earbuds review').
        count: Max videos to return (default 20).

    """
    client = _get_tiktok()
    videos = await client.search_videos(query=query, count=count)
    return [v.model_dump() for v in videos]


@mcp.tool()
async def tiktok_analyze(video_url: str) -> dict:
    """Analyze a TikTok video's engagement metrics.

    Args:
        video_url: Full TikTok video URL (e.g. 'https://www.tiktok.com/@user/video/123456789').

    """
    client = _get_tiktok()
    return await client.analyze_content(video_url=video_url)


@mcp.tool()
async def tiktok_creator(username: str) -> dict:
    """Get TikTok creator profile information.

    Args:
        username: TikTok username without @ (e.g. 'charlidamelio').

    """
    client = _get_tiktok()
    return await client.get_creator_info(username=username)


@mcp.tool()
async def tiktok_hashtag_videos(hashtag: str, count: int = 20) -> list[dict]:
    """Get top videos for a TikTok hashtag.

    Args:
        hashtag: Hashtag name without # (e.g. 'techreview').
        count: Max videos to return (default 20).

    """
    client = _get_tiktok()
    videos = await client.get_hashtag_videos(hashtag=hashtag, count=count)
    return [v.model_dump() for v in videos]


@mcp.tool()
async def tiktok_user_videos(username: str, count: int = 20) -> list[dict]:
    """Get recent videos from a TikTok user.

    Args:
        username: TikTok username without @ (e.g. 'khaby.lame').
        count: Max videos to return (default 20).

    """
    client = _get_tiktok()
    videos = await client.get_user_videos(username=username, count=count)
    return [v.model_dump() for v in videos]


@mcp.tool()
async def social_search(
    query: str, platforms: str = "tiktok", limit: int = 10,
) -> list[dict]:
    """Search across social media platforms.

    Args:
        query: Search query.
        platforms: Comma-separated platform names (default: 'tiktok').
        limit: Max results per platform (default 10).

    """
    agg = _get_aggregator()
    plat_list = [p.strip() for p in platforms.split(",") if p.strip()]
    results = await agg.search_all(query=query, platforms=plat_list, limit=limit)
    return [r.model_dump() for r in results]


@mcp.tool()
async def social_trending(
    platforms: str = "tiktok", category: str = "", limit: int = 20,
) -> list[dict]:
    """Get trending topics across social platforms.

    Args:
        platforms: Comma-separated platform names (default: 'tiktok').
        category: Filter by category (optional).
        limit: Max trends per platform (default 20).

    """
    agg = _get_aggregator()
    plat_list = [p.strip() for p in platforms.split(",") if p.strip()]
    trends = await agg.get_trending(
        platforms=plat_list, category=category, limit=limit,
    )
    return [t.model_dump() for t in trends]


@mcp.tool()
async def social_brand_mentions(
    brand: str, platforms: str = "tiktok", limit: int = 50,
) -> list[dict]:
    """Find brand mentions across social platforms.

    Args:
        brand: Brand or product name to search for.
        platforms: Comma-separated platform names (default: 'tiktok').
        limit: Max mentions per platform (default 50).

    """
    agg = _get_aggregator()
    plat_list = [p.strip() for p in platforms.split(",") if p.strip()]
    mentions = await agg.get_brand_mentions(
        brand=brand, platforms=plat_list, limit=limit,
    )
    return [m.model_dump() for m in mentions]


@mcp.tool()
async def social_hashtag_content(
    hashtag: str, platforms: str = "tiktok", limit: int = 20,
) -> list[dict]:
    """Get content for a hashtag across social platforms.

    Args:
        hashtag: Hashtag to search (with or without #).
        platforms: Comma-separated platform names (default: 'tiktok').
        limit: Max posts per platform (default 20).

    """
    agg = _get_aggregator()
    plat_list = [p.strip() for p in platforms.split(",") if p.strip()]
    clean_tag = hashtag.lstrip("#")
    posts = await agg.get_hashtag_content(
        hashtag=clean_tag, platforms=plat_list, limit=limit,
    )
    return [p.model_dump() for p in posts]
