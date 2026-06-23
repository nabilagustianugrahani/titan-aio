"""Tests for ViMax engine, VariantGenerator, and video pipeline tools."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
class TestViMaxEngine:
    """Test ViMax multi-shot video engine."""

    async def test_fallback_when_vimax_not_installed(self):
        from Services.video.vimax_adapter import ViMaxEngine
        engine = ViMaxEngine(use_vimax=True)  # ViMax won't exist on test env
        result = await engine.generate(script="A nice product demo", hook="Check this out!", duration=15)
        # Should fallback to single-shot
        assert result["model"] in ("wan-2-2", "vimax")
        assert "duration" in result

    async def test_parse_shots(self):
        from Services.video.vimax_adapter import ViMaxEngine
        shots = ViMaxEngine._parse_shots("Scene 1: intro\n\nScene 2: demo\n\nScene 3: outro")
        assert len(shots) == 3
        assert shots[0]["style"] == "closeup"
        assert shots[2]["style"] == "wide"
        assert shots[1]["style"] == "medium"

    async def test_parse_shots_empty(self):
        from Services.video.vimax_adapter import ViMaxEngine
        shots = ViMaxEngine._parse_shots("Single line script")
        assert len(shots) == 1

    async def test_is_available(self):
        from Services.video.vimax_adapter import ViMaxEngine
        # Should not crash, returns bool
        result = ViMaxEngine.is_available()
        assert isinstance(result, bool)

    async def test_max_8_shots(self):
        from Services.video.vimax_adapter import ViMaxEngine
        script = "\n\n".join([f"Scene {i}" for i in range(20)])
        shots = ViMaxEngine._parse_shots(script)
        assert len(shots) <= 8


@pytest.mark.asyncio
class TestVariantGenerator:
    """Test A/B variant generation."""

    async def test_generate_default_variants(self):
        from Services.video.variant_generator import VariantGenerator
        gen = VariantGenerator()
        batch = await gen.generate(
            product_url="https://shopee.co.id/product/test-123",
            product_title="Power Bank 20000mAh",
            num_variants=3,
        )
        assert batch.batch_id
        assert batch.product_title == "Power Bank 20000mAh"
        assert len(batch.variants) == 3
        assert batch.status == "created"

    async def test_variant_labels(self):
        from Services.video.variant_generator import VariantGenerator
        gen = VariantGenerator()
        batch = await gen.generate(
            product_url="https://test.com/p1",
            product_title="Test Product",
            num_variants=4,
        )
        labels = [v.label for v in batch.variants]
        assert labels == ["A", "B", "C", "D"]

    async def test_variant_styles(self):
        from Services.video.variant_generator import VariantGenerator
        gen = VariantGenerator()
        batch = await gen.generate(
            product_url="https://test.com/p1",
            product_title="Test Product",
            num_variants=3,
        )
        styles = [v.style for v in batch.variants]
        assert "bold" in styles
        assert "lifestyle" in styles
        assert "minimal" in styles

    async def test_hooks_are_different(self):
        from Services.video.variant_generator import VariantGenerator
        gen = VariantGenerator()
        batch = await gen.generate(
            product_url="https://test.com/p1",
            product_title="Power Bank",
            num_variants=4,
        )
        hooks = [v.hook for v in batch.variants]
        # Each hook should be unique
        assert len(set(hooks)) == 4

    async def test_scripts_contain_hook(self):
        from Services.video.variant_generator import VariantGenerator
        gen = VariantGenerator()
        batch = await gen.generate(
            product_url="https://test.com/p1",
            product_title="Test Product",
            num_variants=2,
            duration_seconds=30,
        )
        for v in batch.variants:
            assert v.hook in v.script

    async def test_thumbnail_concepts(self):
        from Services.video.variant_generator import VariantGenerator
        gen = VariantGenerator()
        batch = await gen.generate(
            product_url="https://test.com/p1",
            product_title="Power Bank",
            num_variants=3,
        )
        for v in batch.variants:
            assert len(v.thumbnail_concept) > 10
            assert "Power Bank" in v.thumbnail_concept

    async def test_platform_default(self):
        from Services.video.variant_generator import VariantGenerator
        gen = VariantGenerator()
        batch = await gen.generate(
            product_url="https://test.com/p1",
            product_title="Test",
        )
        assert batch.variants[0].platform == "tiktok"

    async def test_variant_ids_unique(self):
        from Services.video.variant_generator import VariantGenerator
        gen = VariantGenerator()
        batch = await gen.generate(
            product_url="https://test.com/p1",
            product_title="Test",
            num_variants=4,
        )
        ids = [v.variant_id for v in batch.variants]
        assert len(set(ids)) == 4


@pytest.mark.asyncio
class TestVariantPublisher:
    """Test variant publishing and optimization."""

    async def test_publish_batch(self):
        from Services.video.variant_generator import VariantGenerator, VariantPublisher
        gen = VariantGenerator()
        pub = VariantPublisher()
        batch = await gen.generate(
            product_url="https://test.com/p1",
            product_title="Test Product",
            num_variants=2,
        )
        tracking = await pub.publish_batch(batch, platforms=["tiktok", "instagram"])
        # Keyed by variant_id, last platform wins
        assert len(tracking) == 2  # 2 variants, each gets last platform
        assert batch.status == "published"

    async def test_analyze_batch(self):
        from Services.video.variant_generator import VariantGenerator, VariantOptimizer
        gen = VariantGenerator()
        opt = VariantOptimizer()
        batch = await gen.generate(
            product_url="https://test.com/p1",
            product_title="Test Product",
            num_variants=3,
        )
        # Simulate metrics
        batch.variants[0].metrics = {"ctr": 0.08, "conversion_rate": 0.05, "spend": 100}
        batch.variants[1].metrics = {"ctr": 0.03, "conversion_rate": 0.02, "spend": 100}
        batch.variants[2].metrics = {"ctr": 0.05, "conversion_rate": 0.03, "spend": 100}

        analysis = await opt.analyze_batch(batch)
        assert analysis["best_variant"]["label"] == "A"  # highest CTR + conv
        assert len(analysis["recommendations"]) > 0
        assert analysis["scale_budget"]
