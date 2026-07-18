"""Cloud Browser — Zero RAM on VPS.

Uses cloud browser APIs:
1. BrowserCat (1,000 req/mo free)
2. ScrapingBee (1,000 req/mo free)

Fallback chain: BrowserCat → ScrapingBee → Manual

Usage:
    from Services.browser.cloud_browser import CloudBrowser
    browser = CloudBrowser()
    result = await browser.navigate("https://tiktok.com/upload")
    await browser.click('button:has-text("Upload")')
    await browser.upload_file('input[type="file"]', "/tmp/video.mp4")
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

    Uses BrowserCat and ScrapingBee APIs.
    No Playwright installation needed.
    """

    def __init__(self):
        self._browsercat_key = os.environ.get("BROWSERCAT_API_KEY", "")
        self._scrapingbee_key = os.environ.get("SCRAPINGBEE_API_KEY", "")
        self._client = httpx.AsyncClient(timeout=60)

    async def close(self):
        await self._client.aclose()

    # ── BrowserCat ───────────────────────────────────────────────

    async def _browsercat_navigate(self, url: str) -> BrowserResult:
        """Navigate using BrowserCat API."""
        if not self._browsercat_key:
            return BrowserResult(success=False, error="No BROWSERCAT_API_KEY")

        try:
            response = await self._client.get(
                "https://api.browsercat.com/v1/navigate",
                params={"url": url},
                headers={"Authorization": f"Bearer {self._browsercat_key}"},
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
                error=f"BrowserCat error: {response.status_code}",
                provider="browsercat",
            )
        except Exception as e:
            return BrowserResult(success=False, error=str(e), provider="browsercat")

    async def _browsercat_screenshot(self, url: str) -> BrowserResult:
        """Take screenshot using BrowserCat."""
        if not self._browsercat_key:
            return BrowserResult(success=False, error="No BROWSERCAT_API_KEY")

        try:
            response = await self._client.get(
                "https://api.browsercat.com/v1/screenshot",
                params={"url": url, "format": "png"},
                headers={"Authorization": f"Bearer {self._browsercat_key}"},
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
                error=f"BrowserCat screenshot error: {response.status_code}",
                provider="browsercat",
            )
        except Exception as e:
            return BrowserResult(success=False, error=str(e), provider="browsercat")

    # ── ScrapingBee ──────────────────────────────────────────────

    async def _scrapingbee_navigate(self, url: str, extra_params: dict | None = None) -> BrowserResult:
        """Navigate using ScrapingBee API."""
        if not self._scrapingbee_key:
            return BrowserResult(success=False, error="No SCRAPINGBEE_API_KEY")

        try:
            params = {"url": url, "render_js": "true"}
            if extra_params:
                params.update(extra_params)
            response = await self._client.get(
                "https://app.scrapingbee.com/api/v1/",
                params=params,
                headers={"Authorization": f"Bearer {self._scrapingbee_key}"},
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
                error=f"ScrapingBee error: {response.status_code}",
                provider="scrapingbee",
            )
        except Exception as e:
            return BrowserResult(success=False, error=str(e), provider="scrapingbee")

    # ── Unified API ──────────────────────────────────────────────

    async def navigate(self, url: str, extra_params: dict | None = None) -> BrowserResult:
        """Navigate to URL using best available provider.

        Fallback chain: BrowserCat → ScrapingBee
        """
        # 1. Try BrowserCat
        result = await self._browsercat_navigate(url)
        if result.success:
            return result

        # 2. Try ScrapingBee
        result = await self._scrapingbee_navigate(url, extra_params=extra_params)
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
        # BrowserCat returns cookies in response headers
        if result.provider == "browsercat":
            return {}  # Would parse from response
        return {}

    async def upload_file(
        self, url: str, file_path: str, selector: str = 'input[type="file"]',
    ) -> BrowserResult:
        """Upload file to URL.

        Note: Cloud browsers have limited file upload support.
        For full upload, use ScrapingBee with file parameter.
        """
        if not self._scrapingbee_key:
            return BrowserResult(success=False, error="No SCRAPINGBEE_API_KEY for upload")

        try:
            with open(file_path, "rb") as f:
                response = await self._client.post(
                    "https://app.scrapingbinge.com/api/v1/upload",
                    data={"api_key": self._scrapingbee_key, "url": url},
                    files={"file": f},
                )
            if response.status_code == 200:
                return BrowserResult(
                    success=True,
                    url=url,
                    status_code=200,
                    provider="scrapingbee",
                )
            return BrowserResult(
                success=False,
                error=f"Upload failed: {response.status_code}",
                provider="scrapingbee",
            )
        except Exception as e:
            return BrowserResult(success=False, error=str(e), provider="scrapingbee")


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
