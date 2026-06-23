"""Test MCP tool functions."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
class TestHealthTool:
    """Test health check tool."""

    async def test_health(self):
        from MCP.tools.health import health
        result = await health()
        assert result.status == "ok"
        assert result.version == "0.1.0"
        assert result.uptime_seconds >= 0


@pytest.mark.asyncio
class TestAnalyzeCompetitors:
    """Test competitor analysis tool."""

    async def test_competitors(self):
        from MCP.tools.analyze_competitors import analyze_competitors
        from MCP.schemas import AnalyzeCompetitorsInput
        result = await analyze_competitors(
            AnalyzeCompetitorsInput(category="elektronik")
        )
        assert result.category == "elektronik"
        assert result.competitors_analyzed > 0
        assert len(result.winning_hooks) > 0


@pytest.mark.asyncio
class TestGenerateOffer:
    """Test offer generation tool."""

    async def test_generate_offer(self):
        from MCP.tools.generate_offer import generate_offer
        from MCP.schemas import GenerateOfferInput, AnalyzeProductOutput
        product = AnalyzeProductOutput(
            product_id="p1", title="Test", price=50000, url="https://test.com"
        )
        result = await generate_offer(
            GenerateOfferInput(product_id="p1", product_analysis=product)
        )
        assert result.product_id == "p1"
        assert result.primary_angle
        assert result.recommended_cta


@pytest.mark.asyncio
class TestGenerateHooks:
    """Test hooks generation tool."""

    async def test_generate_hooks(self):
        from MCP.tools.generate_hooks import generate_hooks
        from MCP.schemas import GenerateHooksInput, GenerateOfferOutput
        offer = GenerateOfferOutput(
            product_id="p1", primary_angle="test", value_proposition="vp"
        )
        result = await generate_hooks(
            GenerateHooksInput(
                product_id="p1", offer_strategy=offer, count=5
            )
        )
        assert len(result.hooks) >= 5
        assert result.product_id == "p1"


@pytest.mark.asyncio
class TestGenerateScript:
    """Test script generation tool."""

    async def test_generate_script(self):
        from MCP.tools.generate_script import generate_script
        from MCP.schemas import GenerateScriptInput, GenerateOfferOutput, Hook
        offer = GenerateOfferOutput(
            product_id="p1", primary_angle="test", value_proposition="vp"
        )
        hooks = [Hook(hook="Test hook", type="curiosity", predicted_ctr="high")]
        result = await generate_script(
            GenerateScriptInput(
                product_id="p1", hooks=hooks, offer_strategy=offer, count=1
            )
        )
        assert len(result.scripts) == 1


@pytest.mark.asyncio
class TestGenerateThumbnail:
    """Test thumbnail generation tool."""

    async def test_thumbnail(self):
        from MCP.tools.generate_thumbnail import generate_thumbnail
        from MCP.schemas import GenerateThumbnailInput
        result = await generate_thumbnail(
            GenerateThumbnailInput(product_id="p1")
        )
        assert result.product_id == "p1"
        assert result.thumbnail.concept


@pytest.mark.asyncio
class TestGenerateImage:
    """Test image generation tool."""

    async def test_image(self):
        from MCP.tools.generate_image import generate_image
        from MCP.schemas import GenerateImageInput
        result = await generate_image(
            GenerateImageInput(prompt="Test image")
        )
        assert result.image_url
        assert result.model_used == "flux-schnell"


@pytest.mark.asyncio
class TestGenerateVideo:
    """Test video generation tool."""

    async def test_video(self):
        from MCP.tools.generate_video import generate_video
        from MCP.schemas import GenerateVideoInput
        result = await generate_video(
            GenerateVideoInput(script="Test script")
        )
        assert result.video_url
        assert result.model_used == "wan2.7-i2v"


@pytest.mark.asyncio
class TestGenerateAvatar:
    """Test avatar generation tool."""

    async def test_avatar(self):
        from MCP.tools.generate_avatar import generate_avatar
        from MCP.schemas import GenerateAvatarInput
        result = await generate_avatar(
            GenerateAvatarInput(persona_name="Tester")
        )
        assert result.avatar_id
        assert result.persona["name"] == "Tester"


@pytest.mark.asyncio
class TestCreateAffiliatePackage:
    """Test full affiliate package creation."""

    async def test_full_package(self):
        from MCP.tools.create_affiliate_package import create_affiliate_package
        from MCP.schemas import CreateAffiliatePackageInput
        result = await create_affiliate_package(
            CreateAffiliatePackageInput(
                url="https://shopee.co.id/test-product-12345"
            )
        )
        assert result.product.title
        assert result.hooks
        assert len(result.hooks.hooks) > 0
        assert result.scripts
        assert len(result.scripts.scripts) > 0
        assert result.thumbnail
        assert result.campaign_id


@pytest.mark.asyncio
class TestVectorStore:
    """Test vector store operations."""

    async def test_add_and_search(self):
        from Services.memory.vector_store import VectorStore
        store = VectorStore()
        ids = store.add_texts(
            "test_collection", ["hello world", "goodbye world"]
        )
        assert len(ids) == 2
        results = store.similarity_search(
            "test_collection", "hello", top_k=1
        )
        assert len(results) > 0
        store.delete_collection("test_collection")
