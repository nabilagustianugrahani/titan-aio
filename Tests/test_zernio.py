"""Tests for Zernio API integration.

Covers:
- ZernioClient configuration and auth
- Account listing and platform routing
- Post creation helpers
- TikTokClient Zernio methods
- AutoUploader Zernio path
- MCP zernio tools (imports only, no live API)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestZernioClient:
    """Zernio API client — unit tests with mocked HTTP."""

    def test_import(self):
        from Services.api.zernio_client import ZernioClient
        assert ZernioClient is not None

    def test_default_values(self):
        from Services.api.zernio_client import ZernioClient

        client = ZernioClient(api_key="sk_test_key")
        assert client._api_key == "sk_test_key"
        assert client.BASE_URL == "https://zernio.com/api/v1"

    def test_is_authenticated_true(self):
        from Services.api.zernio_client import ZernioClient

        client = ZernioClient(api_key="sk_test_key")
        assert client.is_authenticated is True

    def test_is_authenticated_false(self):
        from Services.api.zernio_client import ZernioClient

        client = ZernioClient(api_key="")
        assert client.is_authenticated is False

    def test_video_url_detection(self):
        from Services.api.zernio_client import _is_video_url

        assert _is_video_url("https://example.com/video.mp4") is True
        assert _is_video_url("https://example.com/video.mov") is True
        assert _is_video_url("https://example.com/photo.jpg") is False
        assert _is_video_url("https://example.com/file") is False

    def test_models_accept_extra_fields(self):
        from Services.api.zernio_client import ZernioAccount, ZernioPost, ZernioProfile

        # Should not crash on extra fields or _id from API
        from Services.api.zernio_client import _map_id

        acct = ZernioAccount(**_map_id({"_id": "abc123", "platform": "tiktok"}))
        assert acct.id == "abc123"
        assert acct.platform == "tiktok"

        post = ZernioPost(**_map_id({"_id": "post1", "content": "hello"}))
        assert post.id == "post1"

        prof = ZernioProfile(**_map_id({"_id": "prof1", "name": "Test", "slug": "test"}))
        assert prof.name == "Test"

    def test_get_tiktok_platform_defaults(self):
        from Services.api.zernio_client import ZernioClient

        client = ZernioClient(api_key="sk_test")
        result = client.get_tiktok_platform_defaults(
            privacy_level="PUBLIC",
            allow_comment=True,
            allow_duet=False,
            commercial_content="brand_organic",
        )

        assert result["privacyLevel"] == "PUBLIC"
        assert result["allowComment"] is True
        assert result["allowDuet"] is False
        assert result["commercialContentType"] == "brand_organic"
        assert result["draft"] is False


class TestTikTokClientZernio:
    """TikTokClient Zernio methods — unit tests."""

    @pytest.mark.asyncio
    async def test_get_zernio_no_key(self):
        from Services.api.tiktok_client import TikTokClient

        with patch("titan.config.settings") as mock_settings:
            mock_settings.zernio_api_key_for.return_value = ""
            client = TikTokClient()
            z = await client._get_zernio()
            assert z is None
            await client.close()

    @pytest.mark.asyncio
    async def test_post_video_via_zernio_no_key(self):
        from Services.api.tiktok_client import TikTokClient

        client = TikTokClient()
        result = await client.post_video_via_zernio(
            video_url="https://example.com/video.mp4",
            caption="Test",
        )
        assert "error" in result
        await client.close()

    @pytest.mark.asyncio
    async def test_post_photo_to_tiktok_no_key(self):
        from Services.api.tiktok_client import TikTokClient

        client = TikTokClient()
        result = await client.post_photo_to_tiktok(
            image_urls=["https://example.com/photo.jpg"],
            caption="Test",
        )
        assert "error" in result
        await client.close()

    @pytest.mark.asyncio
    async def test_get_tiktok_analytics_no_key(self):
        from Services.api.tiktok_client import TikTokClient

        client = TikTokClient()
        # Force _zernio to None to simulate no key
        client._zernio = None
        with patch.object(client, '_get_zernio', return_value=None):
            result = await client.get_tiktok_analytics_via_zernio()
            assert "error" in result
        await client.close()


class TestAutoUploaderZernio:
    """AutoUploader Zernio path — unit tests."""

    @pytest.mark.asyncio
    async def test_get_zernio_client_no_key(self):
        from Services.publisher.auto_upload import AutoUploader

        with patch("titan.config.settings") as mock_settings:
            mock_settings.zernio_api_key_for.return_value = ""
            uploader = AutoUploader()
            z = await uploader._get_zernio_client("tiktok")
            assert z is None

    @pytest.mark.asyncio
    async def test_upload_via_zernio_no_key(self):
        from Services.publisher.auto_upload import AutoUploader

        uploader = AutoUploader()
        result = await uploader._upload_via_zernio(
            platform="tiktok",
            caption="Test",
            hashtags=["fyp"],
            media_url="https://example.com/video.mp4",
        )
        assert result.get("status") == "failed"
        assert "error" in result

    @pytest.mark.asyncio
    async def test_upload_fallback_to_browser_no_zernio(self):
        """When Zernio API key missing, upload should report unsupported or fail."""
        from Services.publisher.auto_upload import AutoUploader

        uploader = AutoUploader()
        # No video path, should fail before browser
        result = await uploader.upload(
            platform="tiktok",
            video_path="/nonexistent/video.mp4",
            caption="Test",
        )
        assert result.get("status") == "failed"


class TestZernioMCPTools:
    """Zernio MCP tools — import and signature checks."""

    def test_all_tools_import(self):
        from MCP.tools.zernio_tools import (
            zernio_best_posting_times,
            zernio_check_account_health,
            zernio_create_post,
            zernio_delete_post,
            zernio_get_analytics,
            zernio_get_post,
            zernio_get_tiktok_insights,
            zernio_list_accounts,
            zernio_list_posts,
            zernio_retry_post,
        )
        assert zernio_list_accounts is not None
        assert zernio_create_post is not None
        assert zernio_get_analytics is not None
        assert zernio_get_tiktok_insights is not None
        assert zernio_check_account_health is not None
        assert zernio_list_posts is not None
        assert zernio_get_post is not None
        assert zernio_delete_post is not None
        assert zernio_retry_post is not None
        assert zernio_best_posting_times is not None

    def test_mcp_server_registers_zernio_tools(self):
        """Verify Zernio tools are imported in server.py."""
        import ast
        import os
        from pathlib import Path

        server_path = Path(__file__).resolve().parent.parent / "MCP" / "server.py"
        tree = ast.parse(server_path.read_text())

        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and "zernio" in node.module:
                    for alias in node.names:
                        imports.add(alias.name)

        assert "zernio_list_accounts" in imports
        assert "zernio_create_post" in imports
        assert "zernio_get_analytics" in imports
        assert "zernio_get_tiktok_insights" in imports
        assert "zernio_check_account_health" in imports
        assert "zernio_list_posts" in imports
        assert "zernio_get_post" in imports
        assert "zernio_best_posting_times" in imports


class TestConfigKeyRouting:
    """Platform → API key routing logic."""

    def test_zernio_api_key_for(self):
        from titan.config import Settings

        s = Settings(
            ZERNIO_API_KEY="sk_new",
            ZERNIO_API_KEY_OLD="sk_old",
        )

        assert s.zernio_api_key_for("tiktok") == "sk_old"
        assert s.zernio_api_key_for("facebook") == "sk_old"
        assert s.zernio_api_key_for("instagram") == "sk_new"
        assert s.zernio_api_key_for("youtube") == "sk_new"
        assert s.zernio_api_key_for("twitter") == "sk_new"  # fallback

    def test_zernio_api_key_for_fallback(self):
        """When one key missing, fallback to the other."""
        from titan.config import Settings

        s = Settings(ZERNIO_API_KEY="", ZERNIO_API_KEY_OLD="sk_old")
        assert s.zernio_api_key_for("instagram") == "sk_old"  # fallback
        assert s.zernio_api_key_for("tiktok") == "sk_old"

        s2 = Settings(ZERNIO_API_KEY="sk_new", ZERNIO_API_KEY_OLD="")
        assert s2.zernio_api_key_for("tiktok") == "sk_new"  # fallback
        assert s2.zernio_api_key_for("instagram") == "sk_new"

    def test_zernio_api_key_for_none(self):
        from titan.config import Settings

        s = Settings(ZERNIO_API_KEY="", ZERNIO_API_KEY_OLD="")
        assert s.zernio_api_key_for("tiktok") == ""


class TestConfigProperty:
    """Settings property checks for .env presence."""

    def test_zernio_keys_in_settings(self):
        from titan.config import settings

        # Just check the field exists, values come from .env
        assert hasattr(settings, "ZERNIO_API_KEY")
        assert hasattr(settings, "ZERNIO_API_KEY_OLD")
        assert hasattr(settings, "zernio_api_key_for")
