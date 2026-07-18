"""Test Phase 3 video/avatar/LoRA MCP tools."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
class TestVideoAvatarTools:
    async def test_generate_video(self):
        from MCP.tools.video_avatar_tools import generate_product_video
        result = await generate_product_video("p1", "Test script", "wan2.7-i2v")
        assert "video_id" in result
        assert result["model_used"] == "wan2.7-i2v"

    async def test_generate_avatar(self):
        from MCP.tools.video_avatar_tools import generate_spokesperson_avatar
        result = await generate_spokesperson_avatar("Tester")
        assert "avatar_id" in result
        assert result["persona"]["name"] == "Tester"

    async def test_lora_policy_below_threshold(self):
        from MCP.tools.video_avatar_tools import generate_lora_model
        result = await generate_lora_model("unknown-product-xyz", [])
        assert result["trained"] is False
        assert "below threshold" in result["reason"]

    async def test_tools_import_from_server(self):
        pass
