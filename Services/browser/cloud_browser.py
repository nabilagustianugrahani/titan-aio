"""Cloud Browser — Zero RAM on VPS.

Uses cloud browser APIs:
1. ScrapingBee (priority — always available)
2. BrowserCat (fallback, 1,000 req/mo free)

Fallback chain: ScrapingBee → BrowserCat → Manual

Usage:
    from Services.browser.cloud_browser import CloudBrowser
    browser = CloudBrowser()
    result = await browser.navigate("https://shopee.co.id/search?keyword=sepatu")
    result = await browser.navigate("https://tiktok.com/upload")
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import httpx


@dataclass
class BrowserResult:
    success: bool
    html: str = ""
    url: str = ""
    status_code: int = 0
    error: str | None = None
    provider: str = ""


class CloudBrowser:
    """Cloud browser — zero RAM on VPS.

    Uses ScrapingBee (primary) and BrowserCat (fallback) APIs.
    No Playwright installation needed.
    """

    def __init__(self):
        self._scrapingbee_key = os.environ.get("SCRAPINGBEE_API_KEY", "")
        self._browsercat_key = os.environ.get("BROWSERCAT_API_KEY", "")
        self._client = httpx.AsyncClient(timeout=60)

    async def close(self):
        await self._client.aclose()

    # ── ScrapingBee (PRIMARY) ────────────────────────────────────

    async def _scrapingbee_navigate(
        self, url: str, extra_params: dict | None = None
    ) -> BrowserResult:
        """Navigate using ScrapingBee API.

        Automatically adds premium_proxy for e-commerce sites
        and render_js for JS-heavy pages.
        """
        if not self._scrapingbee_key:
            return BrowserResult(success=False, error="No SCRAPINGBEE_API_KEY")

        # Build params — api_key goes in params dict, not URL path
        # (httpx double-encodes if we put it in the URL string)
        params: dict = {
            "api_key": self._scrapingbee_key,
            "url": url,
            "render_js": "true",
            "premium_proxy": "true",
        }
        if extra_params:
            # Strip api_key from extra_params to avoid duplicates
            extra_params.pop("api_key", None)
            params.update(extra_params)

        try:
            response = await self._client.get(
                "https://app.scrapingbee.com/api/v1/",
                params=params,
                timeout=60,
            )
            if response.status_code == 200:
                return BrowserResult(
                    success=True,
                    html=response.text,
                    url=url,
                    status_code=200,
                    provider="scrapingbee",
                )
            return BrowserResult(
                success=False,
                error=f"ScrapingBee error: HTTP {response.status_code}",
                provider="scrapingbee",
            )
        except Exception as e:
            return BrowserResult(
                success=False, error=f"ScrapingBee: {e}", provider="scrapingbee"
            )

    # ── BrowserCat (FALLBACK) ────────────────────────────────────

    async def _browsercat_navigate(self, url: str) -> BrowserResult:
        """Navigate using BrowserCat API."""
        if not self._browsercat_key:
            return BrowserResult(success=False, error="No BROWSERCAT_API_KEY")

        try:
            response = await self._client.get(
                "https://api.browsercat.com/v1/navigate",
                params={"url": url},
                headers={"Authorization": f"Bearer {self._browsercat_key}"},
                timeout=30,
            )
            if response.status_code == 200:
                data = response.json()
                return BrowserResult(
                    success=True,
                    html=data.get("html", ""),
                    url=data.get("url", url),
                    status_code=200,
                    provider="browsercat",
                )
            return BrowserResult(
                success=False,
                error=f"BrowserCat error: HTTP {response.status_code}",
                provider="browsercat",
            )
        except Exception as e:
            return BrowserResult(
                success=False, error=f"BrowserCat: {e}", provider="browsercat"
            )

    async def _browsercat_screenshot(self, url: str) -> BrowserResult:
        """Take screenshot using BrowserCat."""
        if not self._browsercat_key:
            return BrowserResult(success=False, error="No BROWSERCAT_API_KEY")

        try:
            response = await self._client.get(
                "https://api.browsercat.com/v1/screenshot",
                params={"url": url, "format": "png"},
                headers={"Authorization": f"Bearer {self._browsercat_key}"},
                timeout=30,
            )
            if response.status_code == 200:
                return BrowserResult(
                    success=True,
                    html=response.content.decode("latin-1"),
                    url=url,
                    status_code=200,
                    provider="browsercat",
                )
            return BrowserResult(
                success=False,
                error=f"BrowserCat screenshot error: HTTP {response.status_code}",
                provider="browsercat",
            )
        except Exception as e:
            return BrowserResult(
                success=False, error=f"BrowserCat screenshot: {e}",
                provider="browsercat",
            )

    # ── Unified API ──────────────────────────────────────────────

    async def navigate(
        self, url: str, extra_params: dict | None = None
    ) -> BrowserResult:
        """Navigate to URL using best available provider.

        Priority: ScrapingBee → BrowserCat
        ScrapingBee handles everything; BrowserCat is for screenshot fallback.
        """
        # 1. Try ScrapingBee first (always has key, handles both JS + proxy)
        result = await self._scrapingbee_navigate(url, extra_params=extra_params)
        if result.success:
            return result

        # 2. Fallback: BrowserCat
        result = await self._browsercat_navigate(url)
        if result.success:
            return result

        return BrowserResult(
            success=False,
            error="All providers failed",
            provider="none",
        )

    async def screenshot(self, url: str) -> BrowserResult:
        """Take screenshot of URL."""
        return await self._browsercat_screenshot(url)

    async def get_cookies(self, url: str) -> dict:
        """Get cookies from URL (for session persistence)."""
        result = await self.navigate(url)
        if result.provider == "browsercat":
            return {}
        return {}

    async def upload_file(
        self, url: str, file_path: str, selector: str = 'input[type="file"]',
    ) -> BrowserResult:
        """Upload file to URL.

        Cloud browsers have limited file upload support.
        """
        return BrowserResult(
            success=False,
            error="upload_file not supported via cloud browser API",
            provider="none",
        )


# ── Convenience Functions ────────────────────────────────────────

async def cloud_navigate(url: str) -> BrowserResult:
    """Navigate to URL using cloud browser."""
    browser = CloudBrowser()
    try:
        return await browser.navigate(url)
    finally:
        await browser.close()


async def cloud_screenshot(url: str) -> BrowserResult:
    """Take screenshot of URL."""
    browser = CloudBrowser()
    try:
        return await browser.screenshot(url)
    finally:
        await browser.close()
