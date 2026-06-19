"""Autonomous Pipeline — MCP tools for full autonomous campaign generation."""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional


class AutonomousPipelineInput(BaseModel):
    """Input for autonomous pipeline."""
    product_url: str = Field(description="Shopee/Tokopedia product URL")
    platforms: list[str] = Field(
        default=["tiktok", "instagram", "facebook"],
        description="Target platforms",
    )
    num_variants: int = Field(default=3, ge=1, le=6, description="Number of video variants")
    include_lip_sync: bool = Field(default=False, description="Run lip sync post-production")
    auto_publish: bool = Field(default=True, description="Auto-publish to platforms")


class AutonomousPipelineOutput(BaseModel):
    """Output from autonomous pipeline."""
    pipeline_id: str
    status: str
    product_url: str
    hooks_count: int = 0
    scripts_count: int = 0
    video_count: int = 0
    platform_posts: dict = {}
    notion_url: str = ""
    started_at: str = ""
    completed_at: str = ""
    errors: list[dict] = []


async def run_autonomous_pipeline(input_data: AutonomousPipelineInput) -> AutonomousPipelineOutput:
    """Run the full autonomous pipeline.

    Product URL → Analysis → Content → Video (Google Flow) →
    Post-production (Kaggle) → Publish (6 platforms) → Track

    All 18 agents integrated. Fully autonomous.
    """
    from Services.autonomous_pipeline import AutonomousPipeline

    pipeline = AutonomousPipeline()
    state = await pipeline.run(
        product_url=input_data.product_url,
        platforms=input_data.platforms,
        num_variants=input_data.num_variants,
        include_lip_sync=input_data.include_lip_sync,
        auto_publish=input_data.auto_publish,
    )

    return AutonomousPipelineOutput(
        pipeline_id=state.pipeline_id,
        status=state.status,
        product_url=state.product_url,
        hooks_count=len(state.hooks),
        scripts_count=len(state.scripts),
        video_count=len(state.video_variants),
        platform_posts=state.platform_posts,
        notion_url=state.notion_url,
        started_at=state.started_at,
        completed_at=state.completed_at,
        errors=state.errors,
    )
