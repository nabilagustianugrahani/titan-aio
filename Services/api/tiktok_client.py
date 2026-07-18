"""TikTok API Client — trending content, hashtags, creator data, and posting.

Supports three access modes (in priority order):
1. **Zernio API** — REST API for 14+ social platforms (preferred, no scraping)
2. Official TikTok API (OAuth2) — user-authorised token for posting/user info
3. ScrapingBee proxy — headless browser bypass for IP blocks
4. Public endpoint scraping — direct fallback (often blocked from VPS IPs)
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from urllib.parse import urlencode

import httpx
from pydantic import BaseModel


class TikTokVideo(BaseModel):
    video_id: str = ""
    title: str = ""
    author: str = ""
    author_followers: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    views: int = 0
    hashtags: list[str] = []
    music: str = ""
    duration: int = 0
    created_at: str = ""
    url: str = ""


class TikTokTrend(BaseModel):
    name: str = ""
    hashtag: str = ""
    views: int = 0
    posts_count: int = 0
    category: str = ""


class TikTokClient:
    """TikTok content research & posting client.

    Args:
        client_key: TikTok OAuth client key (for official API).
        client_secret: TikTok OAuth client secret.
        scrapingbee_key: ScrapingBee API key for browser-proxied scraping.
            Falls back to SCRAPINGBEE_API_KEY env-var when empty.
    """

    BASE_URL = "https://www.tiktok.com"
    API_BASE = "https://open-api.tiktok.com"
    SCRAPINGBEE_URL = "https://app.scrapingbee.com/api/v1"

    def __init__(
        self,
        client_key: str = "",
        client_secret: str = "",
        scrapingbee_key: str = "",
    ) -> None:
        self._client: httpx.AsyncClient | None = None
        self.client_key = client_key
        self.client_secret = client_secret
        self._scrapingbee_key = scrapingbee_key or ""
        self._access_token: str = ""
        self._token_expires_at: float = 0
        # Zernio client (lazy-loaded)
        self._zernio: "ZernioClient | None" = None  # type: ignore[name-defined]

    async def _get_zernio(self):
        """Lazy-load Zernio client for posting & analytics."""
        if self._zernio is None:
            from Services.api.zernio_client import ZernioClient
            from titan.config import settings

            key = settings.zernio_api_key_for("tiktok")
            if key:
                self._zernio = ZernioClient(api_key=key)
        return self._zernio

    def _ensure_scrapingbee_key(self) -> str:
        if not self._scrapingbee_key:
            import os
            self._scrapingbee_key = os.environ.get("SCRAPINGBEE_API_KEY", "")
        return self._scrapingbee_key

    async def _scrape_via_scrapingbee(self, url: str) -> str | None:
        """Fetch a URL through ScrapingBee headless browser.

        Returns the rendered HTML/JSON text, or None on failure.
        """
        api_key = self._ensure_scrapingbee_key()
        if not api_key:
            return None
        client = await self._get_client()
        params = {
            "api_key": api_key,
            "url": url,
            "render_js": "true",
            "wait_browser": "3000",
            "premium_proxy": "true",
            "country_code": "us",
        }
        try:
            resp = await client.get(self.SCRAPINGBEE_URL, params=params, timeout=60.0)
            return resp.text if resp.status_code == 200 else None
        except Exception:
            return None

    async def _get_json_via_scrapingbee(self, url: str) -> dict | None:
        """Fetch a JSON API endpoint through ScrapingBee."""
        text = await self._scrape_via_scrapingbee(url)
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    # ── OAuth2 (official API) ──────────────────────────────────────

    async def _ensure_token(self) -> str:
        """Get a fresh OAuth2 access token (auto-refreshes when expired)."""
        if self._access_token and time.time() < self._token_expires_at:
            return self._access_token
        if not self.client_key or not self.client_secret:
            return ""
        client = await self._get_client()
        resp = await client.post(
            f"{self.API_BASE}/oauth/token/",
            data={
                "client_key": self.client_key,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
            },
        )
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            self._access_token = data.get("access_token", "")
            expires_in = data.get("expires_in", 7200)
            self._token_expires_at = time.time() + expires_in - 60
        return self._access_token

    async def _api_request(self, path: str, params: dict | None = None) -> dict:
        """Make an authenticated request to the official TikTok API."""
        token = await self._ensure_token()
        if not token:
            return {"error": "No API credentials configured"}
        client = await self._get_client()
        headers = {"Access-Token": token}
        resp = await client.get(
            f"{self.API_BASE}{path}",
            params=params or {},
            headers=headers,
        )
        data = resp.json() if resp.status_code == 200 else resp.text
        if resp.status_code != 200:
            return {"error": f"API {resp.status_code}", "detail": str(data)}
        payload = data.get("data", data)
        if isinstance(payload, dict) and payload.get("error"):
            return {"error": payload["error"]}
        return payload

    def get_oauth_url(self, redirect_uri: str = "https://localhost:8080/tiktok/callback") -> str:
        """Generate the OAuth URL for user authorization.

        A TikTok user must visit this URL to grant permissions; after
        authorising they are redirected with a ``code`` that can be
        exchanged for a user-level access token.
        """
        params = {
            "client_key": self.client_key,
            "response_type": "code",
            "scope": "user.info.basic,video.upload,video.publish",
            "redirect_uri": redirect_uri,
        }
        return f"https://www.tiktok.com/v2/auth/authorize/?{urlencode(params)}"

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json",
                },
            )
        return self._client

    async def get_trending_hashtags(
        self, category: str = "", limit: int = 20,
    ) -> list[TikTokTrend]:
        """Get trending hashtags on TikTok.

        Tries ScrapingBee proxy first, then direct web scraping, then
        static fallback list.
        """
        # 1 — ScrapingBee proxy
        url = f"{self.BASE_URL}/api/discover/search/?keyword={category or 'trending'}&count={limit}"
        data = await self._get_json_via_scrapingbee(url)
        if data and data.get("data"):
            trends: list[TikTokTrend] = []
            for item in data["data"][:limit]:
                trends.append(
                    TikTokTrend(
                        name=item.get("title", ""),
                        hashtag=f"#{item.get('title', '').replace(' ', '')}",
                        views=item.get("view_count", 0),
                        posts_count=item.get("video_count", 0),
                        category=item.get("category", category or "general"),
                    ),
                )
            if trends:
                return trends

        # 2 — Direct web scraping
        try:
            client = await self._get_client()
            resp = await client.get(
                f"{self.BASE_URL}/api/discover/search/",
                params={"keyword": category or "trending", "count": limit},
            )
            if resp.status_code == 200:
                trends = []
                for item in resp.json().get("data", [])[:limit]:
                    trends.append(
                        TikTokTrend(
                            name=item.get("title", ""),
                            hashtag=f"#{item.get('title', '').replace(' ', '')}",
                            views=item.get("view_count", 0),
                            posts_count=item.get("video_count", 0),
                            category=item.get("category", category or "general"),
                        ),
                    )
                if trends:
                    return trends
        except Exception:
            pass

        # 3 — Static fallback
        fallback: list[TikTokTrend] = [
            TikTokTrend(name="viral", hashtag="#viral", views=500_000_000, category="general"),
            TikTokTrend(name="fyp", hashtag="#fyp", views=400_000_000, category="general"),
            TikTokTrend(name="foryou", hashtag="#foryou", views=350_000_000, category="general"),
            TikTokTrend(name="trending", hashtag="#trending", views=200_000_000, category="general"),
            TikTokTrend(name="reels", hashtag="#reels", views=150_000_000, category="general"),
            TikTokTrend(name="tutorial", hashtag="#tutorial", views=100_000_000, category="education"),
            TikTokTrend(name="review", hashtag="#review", views=80_000_000, category="review"),
            TikTokTrend(name="haul", hashtag="#haul", views=60_000_000, category="fashion"),
            TikTokTrend(name="grwm", hashtag="#grwm", views=50_000_000, category="beauty"),
            TikTokTrend(name="ootd", hashtag="#ootd", views=40_000_000, category="fashion"),
        ]
        if category:
            fallback = [t for t in fallback if t.category == category or t.category == "general"]
        return fallback[:limit]

    async def search_videos(self, query: str, count: int = 20) -> list[TikTokVideo]:
        """Search for videos by keyword.

        Tries ScrapingBee proxy first, then direct scraping.
        """
        search_url = (
            f"{self.BASE_URL}/api/search/general/full/"
            f"?keyword={query}&search_id={hashlib.md5(query.encode()).hexdigest()}&count={count}"
        )

        # 1 — ScrapingBee proxy
        data = await self._get_json_via_scrapingbee(search_url)
        if data and data.get("data"):
            return self._parse_video_list(data["data"], count)

        # 2 — Direct scraping
        try:
            client = await self._get_client()
            search_id = hashlib.md5(query.encode()).hexdigest()
            resp = await client.get(
                f"{self.BASE_URL}/api/search/general/full/",
                params={"keyword": query, "search_id": search_id},
            )
            if resp.status_code == 200:
                data = resp.json()
                return self._parse_video_list(data.get("data", []), count)
        except Exception:
            pass
        return []

    def _parse_video_list(self, items: list, count: int) -> list[TikTokVideo]:
        """Shared parser for TikTok search/user/hashtag video lists."""
        videos: list[TikTokVideo] = []
        for raw in items[:count]:
            item_data = raw if "id" in raw else raw.get("item", raw)
            author = item_data.get("author", {})
            stats = item_data.get("statistics", item_data)
            challenges = item_data.get("challenges", [])
            music_info = item_data.get("music", {})
            videos.append(
                TikTokVideo(
                    video_id=item_data.get("id", ""),
                    title=item_data.get("desc", ""),
                    author=author.get("unique_id", "") or author.get("uniqueId", ""),
                    author_followers=author.get("follower_count", 0) or author.get("followerCount", 0),
                    likes=stats.get("digg_count", 0) or stats.get("diggCount", 0),
                    comments=stats.get("comment_count", 0) or stats.get("commentCount", 0),
                    shares=stats.get("share_count", 0) or stats.get("shareCount", 0),
                    views=stats.get("play_count", 0) or stats.get("playCount", 0),
                    hashtags=[c.get("title", "") for c in challenges],
                    music=music_info.get("title", ""),
                    duration=item_data.get("duration", 0),
                    created_at=item_data.get("create_time", "") or item_data.get("createTime", ""),
                    url=(
                        f"{self.BASE_URL}/@{author.get('unique_id', '') or author.get('uniqueId', '')}"
                        f"/video/{item_data.get('id', '')}"
                    ),
                ),
            )
        return videos

    async def get_creator_info(self, username: str) -> dict:
        """Get creator profile info.

        Tries ScrapingBee proxy first, then direct scraping.
        """
        # 1 — ScrapingBee proxy
        url = f"{self.BASE_URL}/api/user/detail/?uniqueId={username}"
        data = await self._get_json_via_scrapingbee(url)
        if data:
            user = data.get("userInfo", {}).get("user", {})
            if user:
                return {
                    "username": user.get("uniqueId", username),
                    "nickname": user.get("nickname", ""),
                    "followers": user.get("followerCount", 0),
                    "following": user.get("followingCount", 0),
                    "likes": user.get("heartCount", 0),
                    "videos": user.get("videoCount", 0),
                    "verified": user.get("verified", False),
                    "bio": user.get("signature", ""),
                    "avatar": user.get("avatarLarger", ""),
                }

        # 2 — Direct scraping
        try:
            client = await self._get_client()
            resp = await client.get(
                f"{self.BASE_URL}/api/user/detail/",
                params={"uniqueId": username},
            )
            if resp.status_code == 200:
                user = resp.json().get("userInfo", {}).get("user", {})
                return {
                    "username": user.get("uniqueId", username),
                    "nickname": user.get("nickname", ""),
                    "followers": user.get("followerCount", 0),
                    "following": user.get("followingCount", 0),
                    "likes": user.get("heartCount", 0),
                    "videos": user.get("videoCount", 0),
                    "verified": user.get("verified", False),
                    "bio": user.get("signature", ""),
                    "avatar": user.get("avatarLarger", ""),
                }
        except Exception:
            pass
        return {"username": username, "error": "Could not fetch creator info"}

    async def analyze_content(self, video_url: str) -> dict:
        """Analyze a TikTok video's engagement potential."""
        video_id_match = re.search(r"/video/(\d+)", video_url)
        if not video_id_match:
            return {"error": "Invalid video URL — must contain /video/<id>"}

        video_id = video_id_match.group(1)

        def _parse_item(item: dict) -> dict:
            stats = item.get("statistics", {})
            likes = stats.get("diggCount", 0)
            comments = stats.get("commentCount", 0)
            shares = stats.get("shareCount", 0)
            views = stats.get("playCount", 0)
            engagement_rate = round(
                (likes + comments + shares) / max(1, views) * 100, 2,
            )
            author = item.get("author", {})
            return {
                "video_id": video_id,
                "title": item.get("desc", ""),
                "author": author.get("uniqueId", ""),
                "author_followers": author.get("followerCount", 0),
                "views": views,
                "likes": likes,
                "comments": comments,
                "shares": shares,
                "engagement_rate": engagement_rate,
                "viral_score": min(100, int(engagement_rate * 10)),
                "hashtags": [c.get("title", "") for c in item.get("challenges", [])],
                "music": item.get("music", {}).get("title", ""),
                "analysis": (
                    "High engagement" if engagement_rate > 5
                    else "Average engagement" if engagement_rate > 2
                    else "Low engagement"
                ),
            }

        # 1 — ScrapingBee proxy
        sb_url = f"{self.BASE_URL}/api/item/detail/?itemId={video_id}"
        sb_data = await self._get_json_via_scrapingbee(sb_url)
        if sb_data:
            item = sb_data.get("itemInfo", {}).get("itemStruct", {})
            if item:
                return _parse_item(item)

        # 2 — Direct scraping
        try:
            client = await self._get_client()
            resp = await client.get(
                f"{self.BASE_URL}/api/item/detail/",
                params={"itemId": video_id},
            )
            if resp.status_code == 200:
                item = resp.json().get("itemInfo", {}).get("itemStruct", {})
                if item:
                    return _parse_item(item)
        except Exception:
            pass
        return {"video_id": video_id, "error": "Could not analyze video"}

    async def get_hashtag_videos(
        self, hashtag: str, count: int = 20,
    ) -> list[TikTokVideo]:
        """Get videos for a specific hashtag.

        Tries ScrapingBee proxy first, then direct scraping.
        """
        # 1 — ScrapingBee proxy
        sb_url = f"{self.BASE_URL}/api/challenge/item_list/?challengeID={hashtag}&count={count}"
        sb_data = await self._get_json_via_scrapingbee(sb_url)
        if sb_data and sb_data.get("itemList"):
            return self._parse_video_list(sb_data["itemList"], count)

        # 2 — Direct scraping
        try:
            client = await self._get_client()
            resp = await client.get(
                f"{self.BASE_URL}/api/challenge/item_list/",
                params={"challengeID": hashtag, "count": count},
            )
            if resp.status_code == 200:
                data = resp.json()
                return self._parse_video_list(data.get("itemList", []), count)
        except Exception:
            pass
        return []

    async def get_user_videos(
        self, username: str, count: int = 20,
    ) -> list[TikTokVideo]:
        """Get recent videos from a user.

        Tries ScrapingBee proxy first, then direct scraping.
        """
        # 1 — ScrapingBee proxy
        sb_url = f"{self.BASE_URL}/api/post/item_list/?uniqueId={username}&count={count}"
        sb_data = await self._get_json_via_scrapingbee(sb_url)
        if sb_data and sb_data.get("itemList"):
            return self._parse_video_list(sb_data["itemList"], count)

        # 2 — Direct scraping
        try:
            client = await self._get_client()
            resp = await client.get(
                f"{self.BASE_URL}/api/post/item_list/",
                params={"uniqueId": username, "count": count},
            )
            if resp.status_code == 200:
                data = resp.json()
                return self._parse_video_list(data.get("itemList", []), count)
        except Exception:
            pass
        return []

    @property
    def is_authenticated(self) -> bool:
        """Whether official API credentials are configured."""
        return bool(self.client_key and self.client_secret)

    # ── Official API methods ──────────────────────────────────────

    async def get_official_user_info(self, username: str) -> dict:
        """Get user info via the official TikTok Business API."""
        return await self._api_request("/user/info/", {"username": username})

    async def post_video(self, *, video_url: str, caption: str) -> dict:
        """Schedule a video post via TikTok Business API.

        Requires OAuth user token with `video.publish` scope.
        Falls back to error if only client_credentials (app-level) token is set.
        """
        data = await self._api_request("/video/publish/", {
            "source_info": {"source": "PULL_FROM_URL",
                            "video_url": video_url},
            "post_info": {"title": caption, "privacy_level": "PUBLIC"},
        })
        return data

    # ── Zernio-powered posting ─────────────────────────────────────

    async def post_video_via_zernio(
        self,
        video_url: str,
        caption: str,
        account_id: str = "",
        hashtags: list[str] | None = None,
        privacy_level: str = "PUBLIC",
        publish_now: bool = True,
    ) -> dict:
        """Post a video to TikTok via Zernio API.

        Args:
            video_url: Public URL of the video to post.
            caption: Video caption.
            account_id: Zernio social account ID for TikTok. If empty,
                auto-selects the first connected TikTok account.
            hashtags: Optional list of hashtags (without ``#``).
            privacy_level: ``PUBLIC``, ``FRIENDS``, ``SELF_ONLY``.
            publish_now: Post immediately (True) or schedule (False).

        Returns:
            Zernio API response dict with ``post`` containing status.
        """
        zernio = await self._get_zernio()
        if not zernio or not zernio.is_authenticated:
            return {"error": "Zernio not configured — set ZERNIO_API_KEY"}

        if not account_id:
            tiktok_accounts = await zernio.list_accounts(platform="tiktok", status="connected")
            if not tiktok_accounts:
                return {"error": "No connected TikTok account found in Zernio"}
            account_id = tiktok_accounts[0].id

        platform_data = zernio.get_tiktok_platform_defaults(
            privacy_level=privacy_level,
            commercial_content="brand_organic",
        )

        return await zernio.create_post(
            content=caption,
            platform="tiktok",
            account_id=account_id,
            media_urls=[video_url] if video_url else None,
            hashtags=hashtags,
            publish_now=publish_now,
            platform_specific=platform_data,
        )

    async def post_photo_to_tiktok(
        self,
        image_urls: list[str],
        caption: str,
        account_id: str = "",
        hashtags: list[str] | None = None,
        publish_now: bool = True,
    ) -> dict:
        """Post a photo carousel to TikTok via Zernio API.

        Args:
            image_urls: Public URLs of images (max 35 for carousel).
            caption: Post caption.
            account_id: Zernio social account ID for TikTok.
            hashtags: Optional list of hashtags.
            publish_now: Post immediately (True) or schedule (False).

        Returns:
            Zernio API response.
        """
        zernio = await self._get_zernio()
        if not zernio or not zernio.is_authenticated:
            return {"error": "Zernio not configured — set ZERNIO_API_KEY"}

        if not account_id:
            tiktok_accounts = await zernio.list_accounts(platform="tiktok", status="connected")
            if not tiktok_accounts:
                return {"error": "No connected TikTok account found in Zernio"}
            account_id = tiktok_accounts[0].id

        platform_data = zernio.get_tiktok_platform_defaults(
            privacy_level="PUBLIC",
            commercial_content="brand_organic",
        )
        platform_data["mediaType"] = "photo"

        return await zernio.create_post(
            content=caption,
            platform="tiktok",
            account_id=account_id,
            media_urls=image_urls,
            hashtags=hashtags,
            publish_now=publish_now,
            platform_specific=platform_data,
        )

    # ── Zernio-powered analytics ────────────────────────────────────

    async def get_tiktok_analytics_via_zernio(
        self, account_id: str = "",
    ) -> dict:
        """Get TikTok account analytics via Zernio.

        Returns follower count, video count, total likes, profile views.
        """
        zernio = await self._get_zernio()
        if not zernio or not zernio.is_authenticated:
            return {"error": "Zernio not configured"}

        if not account_id:
            tiktok_accounts = await zernio.list_accounts(platform="tiktok", status="connected")
            if not tiktok_accounts:
                return {"error": "No connected TikTok account found"}
            account_id = tiktok_accounts[0].id

        insights = await zernio.get_tiktok_account_insights(account_id)
        if insights:
            return insights.model_dump()
        return {"error": "Could not fetch TikTok insights"}

    # ── Lifecycle ──────────────────────────────────────────────────

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
        if self._zernio:
            await self._zernio.close()
            self._zernio = None
