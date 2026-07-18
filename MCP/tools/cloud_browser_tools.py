"""Cloud Browser — MCP tools for zero-RAM browser automation."""

from __future__ import annotations


from pydantic import BaseModel, Field


class CloudNavigateInput(BaseModel):
    """Input for cloud browser navigation."""

    url: str = Field(description="URL to navigate to")


class CloudNavigateOutput(BaseModel):
    """Output from cloud browser navigation."""

    success: bool
    html: str = ""
    url: str = ""
    status_code: int = 0
    provider: str = ""
    error: str | None = None


class CloudScreenshotInput(BaseModel):
    """Input for cloud browser screenshot."""

    url: str = Field(description="URL to screenshot")


class CloudScreenshotOutput(BaseModel):
    """Output from cloud browser screenshot."""

    success: bool
    url: str = ""
    provider: str = ""
    error: str | None = None


async def cloud_navigate_url(input_data: CloudNavigateInput) -> CloudNavigateOutput:
    """Navigate to URL using cloud browser (BrowserCat → ScrapingBee).

    Zero RAM on VPS. Cloud-based browser automation.
    """
    from Services.browser.cloud_browser import CloudBrowser

    browser = CloudBrowser()
    try:
        result = await browser.navigate(input_data.url)
        return CloudNavigateOutput(
            success=result.success,
            html=result.html[:1000],  # Limit HTML size
            url=result.url,
            status_code=result.status_code,
            provider=result.provider,
            error=result.error,
        )
    finally:
        await browser.close()


async def cloud_screenshot_url(input_data: CloudScreenshotInput) -> CloudScreenshotOutput:
    """Take screenshot of URL using cloud browser.

    Zero RAM on VPS. Cloud-based browser automation.
    """
    from Services.browser.cloud_browser import CloudBrowser

    browser = CloudBrowser()
    try:
        result = await browser.screenshot(input_data.url)
        return CloudScreenshotOutput(
            success=result.success,
            url=result.url,
            provider=result.provider,
            error=result.error,
        )
    finally:
        await browser.close()
