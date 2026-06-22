"""AutoUploader -- BrowserUse-based social media upload agent for TikTok, Instagram, YouTube."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from browser_use import Browser
    from browser_use.config import Config as BrowserConfig
    HAS_BROWSER = True
except ImportError:
    Browser = None
    BrowserConfig = None
    HAS_BROWSER = False

# ---------------------------------------------------------------------------
# Config helper (no hard dep on titan.config; can be used standalone)
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _get_settings() -> dict[str, Any]:
    """Return a flat dict of config values from the environment / .env."""
    from pydantic_settings import BaseSettings

    class _Env(BaseSettings):
        OPENAI_API_KEY: str = ""
        PUBLISHER_SESSIONS_DIR: str = "/tmp/titan-sessions"
        PUBLISHER_HEADLESS: bool = True
        PUBLISHER_UPLOAD_TIMEOUT: int = 120000  # ms
        PUBLISHER_LOGIN_TIMEOUT: int = 120000  # ms

        model_config = {"env_file": str(_PROJECT_ROOT / ".env"), "extra": "ignore"}

    return _Env().model_dump()


# ---------------------------------------------------------------------------
# Uploader
# ---------------------------------------------------------------------------


class AutoUploader:
    """Upload campaign videos to TikTok, Instagram, or YouTube automatically.

    Uses **BrowserUse** with Playwright under the hood.  Sessions are persisted
    so manual login (with 2FA) is needed only once per platform.
    """

    PLATFORMS = frozenset({
        "tiktok", "instagram", "facebook",
    })

    # -- Login URLs ----------------------------------------------------------
    LOGIN_URLS: dict[str, str] = {
        "tiktok": "https://www.tiktok.com/login",
        "instagram": "https://www.instagram.com/",
        "facebook": "https://www.facebook.com/",
    }

    # -- Upload URLs ---------------------------------------------------------
    UPLOAD_URLS: dict[str, str] = {
        "tiktok": "https://www.tiktok.com/upload/",
        "instagram": "https://www.instagram.com/",
        "facebook": "https://www.facebook.com/",
    }

    def __init__(self, sessions_dir: str | Path | None = None) -> None:
        cfg = _get_settings()
        self.sessions_dir = Path(sessions_dir or cfg["PUBLISHER_SESSIONS_DIR"])
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self._headless: bool = cfg["PUBLISHER_HEADLESS"]
        self._upload_timeout: int = cfg["PUBLISHER_UPLOAD_TIMEOUT"]
        self._login_timeout: int = cfg["PUBLISHER_LOGIN_TIMEOUT"]

    # -- Public API ----------------------------------------------------------

    async def upload(
        self,
        platform: str,
        video_path: str,
        caption: str,
        hashtags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Upload a video to *platform*.

        Args:
            platform: One of ``tiktok``, ``instagram``, ``youtube``.
            video_path: Absolute or relative path to the video file.
            caption: Post caption / description text.
            hashtags: Optional list of hashtags (without ``#``).

        Returns:
            A dict with keys:

            - ``url`` -- public URL of the upload (may be approximate).
            - ``status`` -- ``"uploaded"`` | ``"needs_login"`` | ``"failed"``.
            - ``platform`` -- echoed input.
            - ``timestamp`` -- ISO-8601 UTC timestamp.
            - ``error`` -- only present on failure.
        """
        platform = platform.lower().strip()
        if platform not in self.PLATFORMS:
            return self._error(platform, f"Unsupported platform '{platform}'")

        video_path_resolved = self._resolve_video(video_path)
        if video_path_resolved is None:
            return self._error(platform, f"Video file not found: {video_path}")

        full_caption = self._build_caption(caption, hashtags)
        session_file = self.sessions_dir / f"{platform}.json"

        # load saved storage state so cookies persist
        storage_state = self._load_storage(session_file)

        browser = self._create_browser(storage_state=storage_state)

        try:
            await browser.start()

            page = await browser.get_current_page()
            upload_url = self.UPLOAD_URLS[platform]
            await page.goto(upload_url, timeout=self._upload_timeout)
            await page.wait_for_timeout(3000)

            # -- quick login check -------------------------------------------
            if self._is_login_page(page.url, platform):
                return {
                    "url": "",
                    "status": "needs_login",
                    "platform": platform,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "detail": (
                        f"Session expired for {platform}. "
                        f"Run login('{platform}') manually first."
                    ),
                }

            # -- platform-specific upload ------------------------------------
            upload_fn: Any = {
                "tiktok": self._upload_tiktok,
                "instagram": self._upload_instagram,
                "facebook": self._upload_facebook,
            }[platform]

            result = await upload_fn(page, video_path_resolved, full_caption)

            # persist session on success
            if result.get("status") == "uploaded":
                saved = await browser.export_storage_state(path=str(session_file))
                if saved is None:
                    # fallback via cdp
                    state = await browser._cdp_get_storage_state()
                    if state:
                        with open(session_file, "w") as f:
                            json.dump(state, f)

            result.setdefault("platform", platform)
            result.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
            return result

        except Exception as exc:
            return self._error(platform, str(exc))
        finally:
            await browser.close()

    async def login(self, platform: str) -> dict[str, Any]:
        """Open an interactive browser for **manual** login (handles 2FA).

        After the user completes login the session cookies are saved so that
        subsequent ``upload()`` calls can reuse them.

        Returns:
            Dict with ``status``, ``platform``, ``session_file``.
        """
        platform = platform.lower().strip()
        if platform not in self.PLATFORMS:
            return {"error": f"Unsupported platform '{platform}'"}

        url = self.LOGIN_URLS[platform]
        session_file = self.sessions_dir / f"{platform}.json"

        print(f"\n{'='*60}")
        print(f"  Login to {platform.title()} -- complete auth in the browser.")
        print("  After 2FA / login is done, press Enter in this terminal.")
        print(f"{'='*60}\n")

        browser = Browser(
            headless=False,
            disable_security=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )

        try:
            await browser.start()
            page = await browser.get_current_page()
            await page.goto(url, timeout=self._login_timeout)

            # block until the user presses Enter in the terminal
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, lambda: input())

            # save session
            saved = await browser.export_storage_state(path=str(session_file))
            if saved is None:
                state = await browser._cdp_get_storage_state()
                if state:
                    with open(session_file, "w") as f:
                        json.dump(state, f)

            print(f"  Session saved to {session_file}")
            return {
                "status": "logged_in",
                "platform": platform,
                "session_file": str(session_file),
            }
        except Exception as exc:
            return {"error": str(exc), "platform": platform}
        finally:
            await browser.close()

    # -- Internals -----------------------------------------------------------

    def _create_browser(self, storage_state: Any = None) -> Browser:
        return Browser(
            headless=self._headless,
            disable_security=True,
            storage_state=storage_state,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
            ],
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )

    @staticmethod
    def _load_storage(session_file: Path) -> Any:
        """Return loaded storage state, or None so a fresh context is created."""
        if session_file.exists():
            try:
                with open(session_file) as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return None

    @staticmethod
    def _resolve_video(video_path: str) -> str | None:
        p = Path(video_path)
        if p.is_file():
            return str(p.resolve())
        # try relative to project root
        candidate = _PROJECT_ROOT / video_path
        if candidate.is_file():
            return str(candidate.resolve())
        return None

    @staticmethod
    def _build_caption(caption: str, hashtags: list[str] | None) -> str:
        tags_str = " ".join(f"#{t.strip('#')}" for t in (hashtags or []))
        if tags_str:
            return f"{caption}\n\n{tags_str}"
        return caption

    @staticmethod
    def _is_login_page(current_url: str, platform: str) -> bool:
        lowered = current_url.lower()
        triggers: dict[str, list[str]] = {
            "tiktok": ["login", "signin", "passport"],
            "instagram": ["login", "accounts/login"],
            "facebook": ["login", "checkpoint"],
        }
        return any(token in lowered for token in triggers.get(platform, []))

    @staticmethod
    def _error(platform: str, msg: str) -> dict[str, Any]:
        return {
            "url": "",
            "status": "failed",
            "platform": platform,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": msg,
        }

    # -- TikTok --------------------------------------------------------------

    async def _upload_tiktok(
        self, page: Any, video_path: str, caption: str
    ) -> dict[str, Any]:
        """Upload video to TikTok using the /upload page."""
        result: dict[str, Any] = {"status": "failed", "url": ""}

        try:
            # wait for the upload UI to be ready
            await page.wait_for_selector('input[type="file"]', timeout=30_000)
            await page.wait_for_timeout(2000)

            # -- select file -------------------------------------------------
            file_input = page.locator('input[type="file"]')
            await file_input.set_input_files(video_path)
            await page.wait_for_timeout(4000)  # let it process

            # wait for the caption textarea to appear (file loaded)
            await page.wait_for_selector('[data-textarea="true"]', timeout=30_000)
            await page.wait_for_timeout(1000)

            # -- fill caption ------------------------------------------------
            caption_area = page.locator('[data-textarea="true"]')
            await caption_area.click()
            await caption_area.fill("")
            await page.wait_for_timeout(500)
            await caption_area.type(caption, delay=20)

            # -- hit "Post" --------------------------------------------------
            post_btn = page.locator('[data-e2e="post_video"], button:has-text("Post")')
            await post_btn.wait_for(timeout=15_000)
            await post_btn.click()
            await page.wait_for_timeout(5_000)

            result["status"] = "uploaded"
            result["url"] = "https://www.tiktok.com/upload/"

        except Exception as exc:
            result["error"] = str(exc)

        return result

    # -- Instagram -----------------------------------------------------------

    async def _upload_instagram(
        self, page: Any, video_path: str, caption: str
    ) -> dict[str, Any]:
        """Upload a Reel / post to Instagram."""
        result: dict[str, Any] = {"status": "failed", "url": ""}

        try:
            await page.goto(
                "https://www.instagram.com/create/reel/",
                timeout=self._upload_timeout,
            )
            await page.wait_for_timeout(3000)

            # -- select file -------------------------------------------------
            file_input = page.locator('input[type="file"]')
            await file_input.wait_for(timeout=15_000)
            await file_input.set_input_files(video_path)
            await page.wait_for_timeout(5_000)

            # -- click "Next" (crop / edit screen) --------------------------
            next_btn = page.locator('div[role="button"]:has-text("Next")')
            await next_btn.wait_for(timeout=15_000)
            await next_btn.click()
            await page.wait_for_timeout(3_000)

            # -- click "Next" again (details screen) ------------------------
            next_btn2 = page.locator('div[role="button"]:has-text("Next")')
            await next_btn2.wait_for(timeout=15_000)
            await next_btn2.click()
            await page.wait_for_timeout(3_000)

            # -- fill caption ------------------------------------------------
            caption_area = page.locator(
                '[aria-label="Write a caption"], '
                '[role="textbox"][aria-label*="caption"]'
            )
            await caption_area.wait_for(timeout=15_000)
            await caption_area.click()
            await caption_area.fill(caption)
            await page.wait_for_timeout(1_000)

            # -- hit "Share" ------------------------------------------------
            share_btn = page.locator('div[role="button"]:has-text("Share")')
            await share_btn.wait_for(timeout=15_000)
            await share_btn.click()
            await page.wait_for_timeout(5_000)

            result["status"] = "uploaded"
            result["url"] = "https://www.instagram.com/"

        except Exception as exc:
            result["error"] = str(exc)

        return result

    # -- Facebook -------------------------------------------------------------

    async def _upload_facebook(
        self, page: Any, video_path: str, caption: str
    ) -> dict[str, Any]:
        result: dict[str, Any] = {"status": "failed", "url": ""}
        try:
            await page.goto("https://www.facebook.com/", timeout=self._upload_timeout)
            await page.wait_for_timeout(3000)
            photo_video = page.locator('[aria-label="Photo/video"]')
            if not await photo_video.is_visible():
                create_post = page.locator('[role="button"]:has-text("What\'s on your mind")')
                if await create_post.is_visible():
                    await create_post.click()
                    await page.wait_for_timeout(2000)
            if await photo_video.is_visible():
                await photo_video.click()
                await page.wait_for_timeout(2000)
            file_input = page.locator('input[type="file"]')
            await file_input.set_input_files(video_path)
            await page.wait_for_timeout(8000)
            caption_area = page.locator('[role="textbox"]')
            if await caption_area.is_visible():
                await caption_area.click()
                await caption_area.type(caption, delay=10)
            post_btn = page.locator('[aria-label="Post"]')
            if await post_btn.is_visible():
                await post_btn.click()
                await page.wait_for_timeout(5000)
                result["status"] = "uploaded"
                result["url"] = "https://www.facebook.com/"
        except Exception as exc:
            result["error"] = str(exc)
        return result


# ---------------------------------------------------------------------------
# Convenience runner
# ---------------------------------------------------------------------------


async def auto_upload(
    platform: str,
    video_path: str,
    caption: str,
    hashtags: list[str] | None = None,
    sessions_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Shortcut: create an ``AutoUploader`` and upload immediately."""
    uploader = AutoUploader(sessions_dir=sessions_dir)
    return await uploader.upload(platform, video_path, caption, hashtags)


async def auto_login(
    platform: str,
    sessions_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Shortcut: create an ``AutoUploader`` and open interactive login."""
    uploader = AutoUploader(sessions_dir=sessions_dir)
    return await uploader.login(platform)


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Titan AutoUploader (BrowserUse)"
    )
    parser.add_argument(
        "action",
        choices=["upload", "login"],
        help="Action to perform",
    )
    parser.add_argument(
        "--platform",
        required=True,
        choices=["tiktok", "instagram", "facebook", "all"],
    )
    parser.add_argument(
        "--video",
        help="Path to video file (required for upload)",
    )
    parser.add_argument(
        "--caption",
        default="",
        help="Caption / description text",
    )
    parser.add_argument(
        "--hashtags",
        nargs="*",
        help="Space-separated list of hashtags (without #)",
    )
    parser.add_argument(
        "--sessions-dir",
        default="/tmp/titan-sessions",
        help="Directory to store browser session cookies (default: /tmp/titan-sessions)",
    )

    args = parser.parse_args()

    async def _main() -> None:
        if args.action == "login":
            if args.platform == "all":
                results = {}
                for p in AutoUploader.PLATFORMS:
                    results[p] = await auto_login(p, sessions_dir=args.sessions_dir)
                print(json.dumps(results, indent=2))
            else:
                result = await auto_login(
                    args.platform, sessions_dir=args.sessions_dir
                )
                print(json.dumps(result, indent=2))
        else:
            if not args.video:
                parser.error("--video is required for upload")
            if args.platform == "all":
                import asyncio as _a
                from Services.publisher.auto_upload import AutoUploader as _AU
                uploader = _AU(sessions_dir=args.sessions_dir)

                async def _up(plat: str) -> dict[str, Any]:
                    try:
                        return await uploader.upload(plat, args.video, args.caption, args.hashtags)
                    except Exception as exc:
                        return {"platform": plat, "status": "failed", "error": str(exc)}

                results = await _a.gather(*[_up(p) for p in _AU.PLATFORMS])
                print(json.dumps({"results": list(results)}, indent=2))
            else:
                result = await auto_upload(
                    args.platform,
                    args.video,
                    args.caption,
                    hashtags=args.hashtags,
                    sessions_dir=args.sessions_dir,
                )
                print(json.dumps(result, indent=2))

    asyncio.run(_main())
