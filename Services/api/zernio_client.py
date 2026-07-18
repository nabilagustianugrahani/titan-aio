"""Zernio API Client — Social Media API for 14+ platforms.

Zernio provides a unified REST API to post, schedule, retrieve analytics,
and manage content across TikTok, Instagram, Twitter/X, Facebook, LinkedIn,
YouTube, Pinterest, Reddit, Bluesky, Threads, Google Business, Telegram,
Snapchat, WhatsApp, and Discord.

Base URL: https://zernio.com/api/v1
Auth: Bearer token via Authorization header

Docs: https://docs.zernio.com
"""

from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, field_validator

# ── Helpers ───────────────────────────────────────────────────────


def _map_id(data: dict) -> dict:
    """Map ``_id`` from API response to ``id`` for Pydantic models."""
    if "_id" in data and "id" not in data:
        data["id"] = data.pop("_id")
    return data


def _map_ids(items: list[dict]) -> list[dict]:
    return [_map_id(item) for item in items]


def _is_video_url(url: str) -> bool:
    video_ext = (".mp4", ".mov", ".avi", ".webm", ".m4v", ".mkv", ".mpeg")
    return any(url.lower().endswith(ext) for ext in video_ext)


# ── Pydantic models ──────────────────────────────────────────────────


class ZernioAccount(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = ""
    platform: str = ""
    username: str = ""
    displayName: str = ""
    profileUrl: str = ""
    isActive: bool = False
    profileId: dict | None = None
    followerCount: int = 0
    avatar: str = ""


class ZernioProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = ""
    name: str = ""
    slug: str = ""
    description: str = ""


class ZernioPost(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = ""
    title: str = ""
    content: str = ""
    status: str = ""
    scheduledFor: str = ""
    publishedAt: str = ""
    platforms: list[dict] = []
    mediaItems: list[dict] = []
    hashtags: list[str] = []
    tags: list[str] = []
    visibility: str = "public"
    timezone: str = "UTC"
    createdAt: str = ""
    updatedAt: str = ""


class ZernioAnalytics(BaseModel):
    model_config = ConfigDict(extra="ignore")
    impressions: int = 0
    reach: int = 0
    engagement: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    clicks: int = 0
    periodStart: str = ""
    periodEnd: str = ""


class ZernioTikTokInsights(BaseModel):
    model_config = ConfigDict(extra="ignore")
    followerCount: int = 0
    videoCount: int = 0
    totalLikes: int = 0
    profileViews: int = 0
    commentCount: int = 0
    shareCount: int = 0


# ── Client ──────────────────────────────────────────────────────────


class ZernioClient:
    """Client for the Zernio REST API.

    Args:
        api_key: Zernio API key (starts with ``sk_``). Falls back to
            ``ZERNIO_API_KEY`` env-var when empty.
        base_url: API base URL (default https://zernio.com/api/v1).
    """

    BASE_URL = "https://zernio.com/api/v1"

    def __init__(self, api_key: str = "", base_url: str = "") -> None:
        self._client: httpx.AsyncClient | None = None
        self._api_key = api_key
        self._base_url = base_url or self.BASE_URL

    # ── HTTP layer ─────────────────────────────────────────────────

    def _ensure_api_key(self) -> str:
        if not self._api_key:
            import os
            self._api_key = os.environ.get("ZERNIO_API_KEY", "") or os.environ.get("ZERNIO_API_KEY_OLD", "")
        return self._api_key

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=60.0,
                headers={
                    "Authorization": f"Bearer {self._ensure_api_key()}",
                    "User-Agent": "TitanAIO/1.0",
                    "Accept": "application/json",
                },
            )
        return self._client

    async def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        json_data: dict | None = None,
        files: dict | None = None,
    ) -> dict[str, Any]:
        """Make an authenticated request to Zernio API.

        Returns the response JSON dict, or ``{"error": ...}`` on failure.
        """
        api_key = self._ensure_api_key()
        if not api_key:
            return {"error": "ZERNIO_API_KEY not configured"}

        client = await self._get_client()
        url = f"{self._base_url}{path}"

        try:
            resp = await client.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                files=files,
            )
            data: Any = resp.json() if resp.content else {}
            if resp.status_code >= 400:
                detail = data.get("error", data.get("message", str(data)))
                return {"error": f"Zernio {resp.status_code}", "detail": detail}
            return data if isinstance(data, dict) else {"data": data}
        except httpx.HTTPStatusError as exc:
            return {"error": f"HTTP {exc.response.status_code}", "detail": str(exc)}
        except Exception as exc:
            return {"error": "request_failed", "detail": str(exc)}

    async def _request_list(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        json_data: dict | None = None,
    ) -> list:
        """Make an authenticated request and return a list.

        Falls back to empty list on failure.
        """
        result = await self._request(method, path, params=params, json_data=json_data)
        if "error" in result:
            return []
        # Zernio often wraps lists in a key (e.g. {"accounts": [...]})
        for key in ("accounts", "posts", "profiles", "data", "results"):
            if key in result and isinstance(result[key], list):
                return result[key]
        return []

    # ── User & Account ──────────────────────────────────────────────

    async def get_user(self) -> dict[str, Any]:
        """Get the authenticated user."""
        return await self._request("GET", "/user")

    async def list_accounts(
        self,
        platform: str = "",
        status: str = "",
        profile_id: str = "",
    ) -> list[ZernioAccount]:
        """List connected social media accounts.

        Args:
            platform: Filter by platform (``tiktok``, ``instagram``, etc).
            status: ``connected`` or ``disconnected``.
            profile_id: Filter by profile ID.
        """
        params: dict[str, str] = {}
        if platform:
            params["platform"] = platform
        if status:
            params["status"] = status
        if profile_id:
            params["profileId"] = profile_id

        raw = await self._request("GET", "/accounts", params=params)
        accounts_raw: list[dict] = []
        if "error" not in raw:
            accounts_raw = raw.get("accounts", [])

        return [ZernioAccount(**_map_id(a)) for a in accounts_raw]

    async def get_account_health(self, account_id: str) -> dict[str, Any]:
        """Check a specific account's health."""
        return await self._request("GET", f"/accounts/{account_id}/health")

    async def check_accounts_health(self) -> list[dict]:
        """Check health of all accounts."""
        raw = await self._request("GET", "/accounts/health")
        if "error" in raw:
            return []
        return raw.get("accounts", [])

    async def get_tiktok_creator_info(self, account_id: str) -> dict[str, Any]:
        """Get TikTok creator info for a connected account."""
        return await self._request("GET", f"/accounts/{account_id}/tiktok/creator-info")

    # ── Profiles ────────────────────────────────────────────────────

    async def list_profiles(self) -> list[ZernioProfile]:
        """List all profiles (brands/projects)."""
        raw = await self._request("GET", "/profiles")
        profiles_raw: list[dict] = []
        if "error" not in raw:
            profiles_raw = raw.get("profiles", [])
        return [ZernioProfile(**_map_id(p)) for p in profiles_raw]

    # ── Posts ───────────────────────────────────────────────────────

    async def create_post(
        self,
        content: str,
        platform: str,
        account_id: str,
        media_urls: list[str] | None = None,
        title: str = "",
        scheduled_at: str = "",
        hashtags: list[str] | None = None,
        publish_now: bool = True,
        platform_specific: dict | None = None,
        custom_content: str = "",
    ) -> dict[str, Any]:
        """Create and publish (or schedule) a post.

        Args:
            content: Post caption/text.
            platform: Target platform (``tiktok``, ``instagram``, etc).
            account_id: Zernio social account ID.
            media_urls: Public URLs of media to attach.
            title: Optional post title.
            scheduled_at: ISO-8601 datetime for scheduling.
            hashtags: List of hashtags (with or without ``#``).
            publish_now: When True, publish immediately. When False and
                ``scheduled_at`` is set, schedule for that time.
            platform_specific: Platform-specific data (privacy level,
                allow comments, etc).
            custom_content: Platform-specific text override.
        """
        platforms: list[dict[str, Any]] = [
            {
                "platform": platform,
                "accountId": account_id,
            },
        ]
        if custom_content:
            platforms[0]["customContent"] = custom_content
        if platform_specific:
            platforms[0]["platformSpecificData"] = platform_specific

        body: dict[str, Any] = {
            "content": content,
            "platforms": platforms,
            "publishNow": publish_now,
        }
        if title:
            body["title"] = title
        if scheduled_at and not publish_now:
            body["scheduledFor"] = scheduled_at
            body.pop("publishNow", None)
        if hashtags:
            body["hashtags"] = [h.lstrip("#") for h in hashtags]
        if media_urls:
            body["mediaItems"] = [
                {"type": "video" if _is_video_url(u) else "image", "url": u}
                for u in media_urls
            ]

        return await self._request("POST", "/posts", json_data=body)

    async def list_posts(
        self,
        status: str = "",
        platform: str = "",
        limit: int = 20,
        page: int = 1,
    ) -> list[ZernioPost]:
        """List posts.

        Args:
            status: Filter by status (``published``, ``scheduled``, etc).
            platform: Filter by platform.
            limit: Results per page (max 100).
            page: Page number (1-based).
        """
        params: dict[str, Any] = {"limit": min(limit, 100), "page": page}
        if status:
            params["status"] = status
        if platform:
            params["platform"] = platform

        raw = await self._request("GET", "/posts", params=params)
        posts_raw: list[dict] = []
        if "error" not in raw:
            posts_raw = raw.get("posts", [])
        return [ZernioPost(**_map_id(p)) for p in posts_raw]

    async def get_post(self, post_id: str) -> ZernioPost | None:
        """Get a single post by ID."""
        raw = await self._request("GET", f"/posts/{post_id}")
        if "error" in raw:
            return None
        post_raw = raw.get("post", raw)
        return ZernioPost(**_map_id(post_raw))

    async def delete_post(self, post_id: str) -> dict[str, Any]:
        """Delete a post."""
        return await self._request("DELETE", f"/posts/{post_id}")

    async def retry_post(self, post_id: str) -> dict[str, Any]:
        """Retry a failed post."""
        return await self._request("POST", f"/posts/{post_id}/retry")

    # ── Media Upload ────────────────────────────────────────────────

    async def presign_upload(
        self,
        filename: str,
        content_type: str,
        size: int = 0,
    ) -> dict[str, Any]:
        """Get a presigned URL to upload a file (up to 5GB).

        Returns ``{uploadUrl, publicUrl, key, expiresIn}``.
        Use ``uploadUrl`` with a PUT request (binary body) to upload.
        The resulting ``publicUrl`` can be used in ``create_post``.
        """
        body: dict[str, Any] = {
            "filename": filename,
            "contentType": content_type,
        }
        if size:
            body["size"] = size
        return await self._request("POST", "/media/presign", json_data=body)

    async def upload_direct(
        self,
        file_content: bytes,
        filename: str,
        content_type: str = "",
    ) -> dict[str, Any]:
        """Upload a file directly (max 25MB).

        Returns ``{url, filename, contentType, size}``.
        The returned ``url`` can be used in ``create_post``.

        For files larger than 25MB, use ``presign_upload()`` instead.
        """
        files = {"file": (filename, file_content, content_type or "application/octet-stream")}
        return await self._request("POST", "/media/upload-direct", files=files)

    async def upload_from_url(self, url: str) -> dict[str, Any]:
        """Import media from a public URL into Zernio storage.

        Zernio fetches the file and returns a hosted URL.
        """
        return await self._request(
            "POST",
            "/tools/validate/media",
            json_data={"url": url},
        )

    # ── Analytics ───────────────────────────────────────────────────

    async def get_analytics(
        self,
        platform: str = "",
        period_start: str = "",
        period_end: str = "",
    ) -> list[ZernioAnalytics]:
        """Get post analytics."""
        params: dict[str, str] = {}
        if platform:
            params["platform"] = platform
        if period_start:
            params["periodStart"] = period_start
        if period_end:
            params["periodEnd"] = period_end

        raw = await self._request("GET", "/analytics", params=params)
        analytics_raw: list[dict] = []
        if "error" not in raw:
            analytics_raw = raw.get("analytics", raw.get("data", []))
        return [ZernioAnalytics(**a) for a in analytics_raw] if analytics_raw else []

    async def get_tiktok_account_insights(self, account_id: str) -> ZernioTikTokInsights | None:
        """Get TikTok account-level insights."""
        raw = await self._request("GET", f"/analytics/tiktok/account-insights",
                                   params={"accountId": account_id})
        if "error" in raw:
            return None
        return ZernioTikTokInsights(**raw)

    async def get_daily_metrics(
        self,
        platform: str = "",
        days: int = 7,
    ) -> list[dict]:
        """Get daily aggregated metrics."""
        params: dict[str, Any] = {"days": days}
        if platform:
            params["platform"] = platform
        raw = await self._request("GET", "/analytics/daily-metrics", params=params)
        if "error" in raw:
            return []
        return raw.get("metrics", raw.get("data", []))

    async def get_best_times_to_post(
        self,
        platform: str = "tiktok",
        days: int = 7,
    ) -> list[dict]:
        """Get best times to post based on engagement data."""
        raw = await self._request(
            "GET",
            "/analytics/best-time",
            params={"platform": platform, "days": days},
        )
        if "error" in raw:
            return []
        return raw.get("times", raw.get("data", []))

    # ── TikTok-specific ─────────────────────────────────────────────

    def get_tiktok_platform_defaults(
        self,
        privacy_level: str = "PUBLIC",
        allow_comment: bool = True,
        allow_duet: bool = True,
        allow_stitch: bool = True,
        commercial_content: str = "none",
        draft: bool = False,
    ) -> dict[str, Any]:
        """Return TikTok platform-specific data for use in ``create_post``.

        Args:
            privacy_level: ``PUBLIC``, ``FRIENDS``, ``SELF_ONLY``.
            allow_comment: Allow comments.
            allow_duet: Allow duets.
            allow_stitch: Allow stitches.
            commercial_content: ``none``, ``brand_organic``, ``brand_content``.
            draft: Send to Creator Inbox instead of publishing.
        """
        return {
            "privacyLevel": privacy_level,
            "allowComment": allow_comment,
            "allowDuet": allow_duet,
            "allowStitch": allow_stitch,
            "commercialContentType": commercial_content,
            "draft": draft,
        }

    # ── Connection status ───────────────────────────────────────────

    @property
    def is_authenticated(self) -> bool:
        """Whether the API key is configured."""
        return bool(self._ensure_api_key())

    # ── Lifecycle ───────────────────────────────────────────────────

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None


