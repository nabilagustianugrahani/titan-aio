"""Social Media Aggregator — unified interface for TikTok, Instagram, Twitter."""

from __future__ import annotations

from pydantic import BaseModel


class SocialPost(BaseModel):
    platform: str
    post_id: str = ""
    author: str = ""
    content: str = ""
    likes: int = 0
    comments: int = 0
    shares: int = 0
    views: int = 0
    hashtags: list[str] = []
    url: str = ""
    created_at: str = ""
    engagement_rate: float = 0.0


class SocialTrend(BaseModel):
    platform: str
    name: str
    posts_count: int = 0
    engagement_score: float = 0.0
    category: str = ""


class SocialAggregator:
    """Unified social media data aggregation."""

    def __init__(self) -> None:
        self._tiktok_client = None

    async def _get_tiktok(self):  # type: ignore[no-untyped-def]
        if self._tiktok_client is None:
            from Services.api.tiktok_client import TikTokClient
            from titan.config import settings

            self._tiktok_client = TikTokClient(
                client_key=settings.TIKTOK_CLIENT_KEY,
                client_secret=settings.TIKTOK_CLIENT_SECRET,
                scrapingbee_key=settings.SCRAPINGBEE_API_KEY,
            )
        return self._tiktok_client

    async def search_all(
        self,
        query: str,
        platforms: list[str] | None = None,
        limit: int = 10,
    ) -> list[SocialPost]:
        """Search across all platforms."""
        platforms = platforms or ["tiktok"]
        results: list[SocialPost] = []

        if "tiktok" in platforms:
            tiktok = await self._get_tiktok()
            videos = await tiktok.search_videos(query=query, count=limit)
            for v in videos:
                total = v.likes + v.comments + v.shares
                engagement = round(total / max(1, v.views) * 100, 2) if v.views else 0
                results.append(
                    SocialPost(
                        platform="tiktok",
                        post_id=v.video_id,
                        author=v.author,
                        content=v.title,
                        likes=v.likes,
                        comments=v.comments,
                        shares=v.shares,
                        views=v.views,
                        hashtags=v.hashtags,
                        url=v.url,
                        created_at=v.created_at,
                        engagement_rate=engagement,
                    ),
                )

        return results

    async def get_trending(
        self,
        platforms: list[str] | None = None,
        category: str = "",
        limit: int = 20,
    ) -> list[SocialTrend]:
        """Get trending topics across platforms."""
        platforms = platforms or ["tiktok"]
        trends: list[SocialTrend] = []

        if "tiktok" in platforms:
            tiktok = await self._get_tiktok()
            tt_trends = await tiktok.get_trending_hashtags(
                category=category, limit=limit,
            )
            for t in tt_trends:
                trends.append(
                    SocialTrend(
                        platform="tiktok",
                        name=t.name,
                        posts_count=t.posts_count,
                        engagement_score=t.views / 1_000_000,
                        category=t.category,
                    ),
                )

        return trends

    async def get_brand_mentions(
        self,
        brand: str,
        platforms: list[str] | None = None,
        limit: int = 50,
    ) -> list[SocialPost]:
        """Get mentions of a brand across platforms."""
        return await self.search_all(
            query=brand, platforms=platforms, limit=limit,
        )

    async def get_hashtag_content(
        self,
        hashtag: str,
        platforms: list[str] | None = None,
        limit: int = 20,
    ) -> list[SocialPost]:
        """Get content for a hashtag across platforms."""
        platforms = platforms or ["tiktok"]
        results: list[SocialPost] = []

        if "tiktok" in platforms:
            tiktok = await self._get_tiktok()
            videos = await tiktok.get_hashtag_videos(
                hashtag=hashtag, count=limit,
            )
            for v in videos:
                total = v.likes + v.comments + v.shares
                engagement = round(total / max(1, v.views) * 100, 2) if v.views else 0
                results.append(
                    SocialPost(
                        platform="tiktok",
                        post_id=v.video_id,
                        author=v.author,
                        content=v.title,
                        likes=v.likes,
                        comments=v.comments,
                        shares=v.shares,
                        views=v.views,
                        hashtags=v.hashtags,
                        url=v.url,
                        created_at=v.created_at,
                        engagement_rate=engagement,
                    ),
                )

        return results

    async def close(self) -> None:
        """Close all underlying API clients."""
        if self._tiktok_client:
            await self._tiktok_client.close()
            self._tiktok_client = None
