"""Viral Prediction — MCP tool wrapper for the Viral Predictor service."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from Services.agents.viral_predictor import ViralInput, ViralPredictor


class PredictViralityInput(BaseModel):
    """Input for virality prediction."""

    hook: str = Field(description="First line / hook of the content")
    script: str = Field(default="", description="Full script body")
    platform: str = Field(default="tiktok", description="Target platform (tiktok/instagram/facebook/youtube/twitter)")
    niche: str = Field(default="general", description="Content niche (electronics/fashion/beauty/food/fitness/tech/finance/education/entertainment)")


class PredictViralityOutput(BaseModel):
    """Output from virality prediction."""

    score: int = Field(description="Overall virality score 0-100")
    predicted_reach: int = Field(description="Predicted impressions within 48h")
    predicted_engagement_rate: float = Field(description="Predicted engagement rate %")
    best_posting_time: str = Field(description="Recommended posting time (HH:MM UTC)")
    platform_scores: dict[str, int] = Field(description="Score per platform")
    optimization_tips: list[str] = Field(description="Actionable improvement tips")
    confidence: float = Field(description="Prediction confidence 0-1")
    feature_breakdown: dict[str, float] = Field(description="Per-feature score contribution")


_predictor: ViralPredictor | None = None


def _get_predictor() -> ViralPredictor:
    global _predictor
    if _predictor is None:
        _predictor = ViralPredictor()
    return _predictor


async def predict_virality(
    hook: str,
    script: str = "",
    platform: str = "tiktok",
    niche: str = "general",
) -> PredictViralityOutput:
    """Score content virality before publishing.

    Analyzes 22 features including hook strength, emotional impact,
    curiosity gap, power words, CTA placement, and more.
    Returns a 0-100 score with per-platform breakdown and optimization tips.
    """
    input_data = ViralInput(
        hook=hook,
        script=script,
        platform=platform,
        niche=niche,
    )

    predictor = _get_predictor()
    result = await predictor.predict(input_data)

    return PredictViralityOutput(
        score=result.score,
        predicted_reach=result.predicted_reach,
        predicted_engagement_rate=result.predicted_engagement_rate,
        best_posting_time=result.best_posting_time,
        platform_scores=result.platform_scores,
        optimization_tips=result.optimization_tips,
        confidence=result.confidence,
        feature_breakdown=result.feature_breakdown,
    )
