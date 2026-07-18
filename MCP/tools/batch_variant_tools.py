"""Batch Variant Generation — MCP tools for A/B testing."""

from __future__ import annotations

from pydantic import BaseModel, Field


class BatchVariantInput(BaseModel):
    """Input for batch variant generation."""

    product_url: str = Field(description="Product URL to generate variants for")
    product_title: str = Field(default="", description="Product title (auto-fetched if empty)")
    num_variants: int = Field(default=3, ge=2, le=6, description="Number of A/B variants (2-6)")
    platforms: list[str] = Field(default=["tiktok"], description="Target platforms")
    duration_seconds: int = Field(default=30, description="Video duration in seconds")


class BatchVariantOutput(BaseModel):
    """Output from batch variant generation."""

    batch_id: str
    product_id: str
    product_title: str
    variants: list[dict]
    status: str = "created"


class AnalyzeBatchInput(BaseModel):
    """Input for batch analysis."""

    batch_id: str = Field(description="Batch ID to analyze")


class AnalyzeBatchOutput(BaseModel):
    """Output from batch analysis."""

    batch_id: str
    total_variants: int
    best_variant: dict
    recommendations: list[str]
    scale_budget: dict


async def generate_batch_variants(input_data: BatchVariantInput) -> BatchVariantOutput:
    """Generate multiple A/B variants for a product.

    Each variant gets unique hook, script, style, and thumbnail concept.
    Use for A/B testing across platforms.
    """
    from Services.video.variant_generator import VariantGenerator

    gen = VariantGenerator()
    batch = await gen.generate(
        product_url=input_data.product_url,
        product_title=input_data.product_title,
        num_variants=input_data.num_variants,
        platforms=input_data.platforms,
        duration_seconds=input_data.duration_seconds,
    )

    return BatchVariantOutput(
        batch_id=batch.batch_id,
        product_id=batch.product_id,
        product_title=batch.product_title,
        variants=[
            {
                "variant_id": v.variant_id,
                "label": v.label,
                "hook": v.hook,
                "script": v.script,
                "style": v.style,
                "thumbnail_concept": v.thumbnail_concept,
                "platform": v.platform,
            }
            for v in batch.variants
        ],
        status=batch.status,
    )


async def analyze_batch_performance(input_data: AnalyzeBatchInput) -> AnalyzeBatchOutput:
    """Analyze A/B test results and recommend winner."""
    from Services.video.variant_generator import VariantOptimizer

    # In production, load batch from DB
    # For now, return placeholder analysis
    VariantOptimizer()

    return AnalyzeBatchOutput(
        batch_id=input_data.batch_id,
        total_variants=0,
        best_variant={"label": "A", "style": "bold", "ctr": 0.0},
        recommendations=["Collect more data before optimizing"],
        scale_budget={},
    )
