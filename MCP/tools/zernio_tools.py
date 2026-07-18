"""MCP tools for Zernio — Social Media API.

Provides tools for:
- Listing connected social accounts
- Creating/publishing posts
- Getting analytics
- Checking account health
- TikTok-specific insights
"""

from __future__ import annotations

from MCP.instance import mcp

# Two cached clients: one per API key
_zernio_key1 = None   # Instagram, YouTube
_zernio_key2 = None   # TikTok, Facebook


def _get_zernio(platform: str = ""):
    """Return the right Zernio client for *platform*.

    Key 1 → Instagram, YouTube
    Key 2 → TikTok, Facebook
    """
    from Services.api.zernio_client import ZernioClient
    from titan.config import settings

    platform = platform.lower().strip()

    # Determine which key to use
    if platform in ("instagram", "youtube"):
        want_old = False
    elif platform in ("tiktok", "facebook"):
        want_old = True
    else:
        # No platform / unknown → use whichever is set, prefer key2 (old) since
        # it has more accounts. Fallback to the other.
        want_old = bool(settings.ZERNIO_API_KEY_OLD)

    if want_old:
        global _zernio_key2
        if _zernio_key2 is None:
            key = settings.ZERNIO_API_KEY_OLD or settings.ZERNIO_API_KEY
            if key:
                _zernio_key2 = ZernioClient(api_key=key)
        return _zernio_key2
    else:
        global _zernio_key1
        if _zernio_key1 is None:
            key = settings.ZERNIO_API_KEY or settings.ZERNIO_API_KEY_OLD
            if key:
                _zernio_key1 = ZernioClient(api_key=key)
        return _zernio_key1


@mcp.tool()
async def zernio_list_accounts(
    platform: str = "",
    status: str = "connected",
) -> list[dict]:
    """List connected social media accounts via Zernio.

    Args:
        platform: Filter by platform (e.g. 'tiktok', 'instagram', 'twitter').
            Empty = all platforms.
        status: Filter by status ('connected', 'disconnected'). Default 'connected'.

    Returns list of accounts with platform, username, displayName, isActive.
    """
    z = _get_zernio(platform)
    if not z or not z.is_authenticated:
        return [{"error": "ZERNIO_API_KEY not configured"}]
    accounts = await z.list_accounts(platform=platform or "", status=status or "")
    return [a.model_dump() for a in accounts]


@mcp.tool()
async def zernio_create_post(
    content: str,
    platform: str,
    account_id: str = "",
    media_urls: str = "",
    title: str = "",
    hashtags: str = "",
    publish_now: bool = True,
    privacy_level: str = "PUBLIC",
) -> dict:
    """Create and publish a social media post via Zernio.

    Args:
        content: Post caption/text content.
        platform: Target platform (e.g. 'tiktok', 'instagram', 'twitter',
            'facebook', 'linkedin', 'youtube').
        account_id: Zernio social account ID. If empty, auto-selects the
            first connected account for the platform.
        media_urls: Comma-separated public URLs of media to attach.
        title: Optional post title.
        hashtags: Space-separated list of hashtags (with or without #).
        publish_now: Publish immediately (default True). Set False to
            create as draft/scheduled.
        privacy_level: Privacy setting — 'PUBLIC', 'FRIENDS', 'SELF_ONLY'.

    Returns created post with status, platform URLs, and Zernio post ID.
    """
    z = _get_zernio(platform)
    if not z or not z.is_authenticated:
        return {"error": "ZERNIO_API_KEY not configured"}

    if not account_id:
        accounts = await z.list_accounts(platform=platform, status="connected")
        if not accounts:
            return {"error": f"No connected {platform} account found"}
        account_id = accounts[0].id

    media_list = [u.strip() for u in media_urls.split(",") if u.strip()] if media_urls else None
    hashtag_list = [h.strip().lstrip("#") for h in hashtags.split() if h.strip()] if hashtags else None

    platform_data = None
    if platform == "tiktok":
        platform_data = z.get_tiktok_platform_defaults(
            privacy_level=privacy_level,
            commercial_content="brand_organic",
        )

    result = await z.create_post(
        content=content,
        platform=platform,
        account_id=account_id,
        media_urls=media_list,
        title=title,
        hashtags=hashtag_list,
        publish_now=publish_now,
        platform_specific=platform_data,
    )

    return result


@mcp.tool()
async def zernio_list_posts(
    status: str = "",
    platform: str = "",
    limit: int = 20,
) -> list[dict]:
    """List recent posts from Zernio.

    Args:
        status: Filter by status ('published', 'scheduled', 'draft',
            'failed', 'partial'). Empty = all.
        platform: Filter by platform (e.g. 'tiktok').
        limit: Max results (default 20, max 100).

    Returns list of posts with content, status, platform URLs, timestamps.
    """
    z = _get_zernio(platform)
    if not z or not z.is_authenticated:
        return [{"error": "ZERNIO_API_KEY not configured"}]
    posts = await z.list_posts(status=status, platform=platform, limit=limit)
    return [p.model_dump() for p in posts]


@mcp.tool()
async def zernio_get_post(post_id: str) -> dict:
    """Get a single post's details by Zernio post ID.

    Args:
        post_id: The Zernio post ID (from zernio_list_posts or
            zernio_create_post response).

    Returns full post object with platform statuses, URLs.
    """
    z = _get_zernio()  # no platform context for a single post ID
    if not z or not z.is_authenticated:
        return {"error": "ZERNIO_API_KEY not configured"}
    post = await z.get_post(post_id=post_id)
    if post is None:
        return {"error": "Post not found"}
    return post.model_dump()


@mcp.tool()
async def zernio_delete_post(post_id: str) -> dict:
    """Delete a Zernio post by ID.

    Args:
        post_id: The Zernio post ID to delete.

    Returns confirmation message.
    """
    z = _get_zernio()
    if not z or not z.is_authenticated:
        return {"error": "ZERNIO_API_KEY not configured"}
    return await z.delete_post(post_id=post_id)




@mcp.tool()
async def zernio_retry_post(post_id: str) -> dict:
    """Retry a failed Zernio post.

    Args:
        post_id: The Zernio post ID to retry.

    Returns updated post status.
    """
    z = _get_zernio()
    if not z or not z.is_authenticated:
        return {"error": "ZERNIO_API_KEY not configured"}
    return await z.retry_post(post_id=post_id)




@mcp.tool()
async def zernio_get_tiktok_insights(account_id: str = "") -> dict:
    """Get TikTok account-level analytics via Zernio.

    Args:
        account_id: Zernio TikTok account ID. If empty, auto-selects
            the first connected TikTok account.

    Returns follower count, video count, total likes, profile views.
    """
    z = _get_zernio("tiktok")
    if not z or not z.is_authenticated:
        return {"error": "ZERNIO_API_KEY not configured"}

    if not account_id:
        accounts = await z.list_accounts(platform="tiktok", status="connected")
        if not accounts:
            return {"error": "No connected TikTok account found"}
        account_id = accounts[0].id

    insights = await z.get_tiktok_account_insights(account_id)
    if insights is None:
        return {"error": "Could not fetch TikTok insights"}
    return insights.model_dump()


@mcp.tool()
async def zernio_get_analytics(
    platform: str = "",
    days: int = 7,
) -> dict:
    """Get aggregated social media analytics via Zernio.

    Args:
        platform: Filter by platform (e.g. 'tiktok', 'instagram'). Empty = all.
        days: Number of days to look back (default 7).

    Returns daily metrics with impressions, reach, engagement, likes,
    comments, shares.
    """
    z = _get_zernio(platform)
    if not z or not z.is_authenticated:
        return {"error": "ZERNIO_API_KEY not configured"}
    metrics = await z.get_daily_metrics(platform=platform, days=days)
    return {"platform": platform, "days": days, "metrics": metrics}


@mcp.tool()
async def zernio_best_posting_times(
    platform: str = "tiktok",
    days: int = 7,
) -> list[dict]:
    """Get the best times to post based on historical engagement.

    Args:
        platform: Platform to analyze (default 'tiktok').
        days: Days of data to analyze (default 7).

    Returns list of optimal posting times with predicted engagement.
    """
    z = _get_zernio(platform)
    if not z or not z.is_authenticated:
        return [{"error": "ZERNIO_API_KEY not configured"}]
    return await z.get_best_times_to_post(platform=platform, days=days)


@mcp.tool()
async def zernio_check_account_health(
    account_id: str = "",
    platform: str = "",
) -> dict:
    """Check health status of Zernio-connected social accounts.

    Args:
        account_id: Specific account ID to check. If empty, checks all
            accounts for the specified platform.
        platform: Filter by platform (e.g. 'tiktok'). Only used when
            account_id is empty.

    Returns account health status: connected/disconnected, errors.
    """
    z = _get_zernio(platform)
    if not z or not z.is_authenticated:
        return {"error": "ZERNIO_API_KEY not configured"}

    if account_id:
        return await z.get_account_health(account_id=account_id)

    # Check all or platform-filtered
    accounts = await z.list_accounts(platform=platform or "", status="")
    results = []
    for acct in accounts:
        health = await z.get_account_health(acct.id)
        results.append({
            "account_id": acct.id,
            "platform": acct.platform,
            "username": acct.username,
            "health": health,
        })
    return {"accounts": results}
