"""SharedState — typed state container for pipeline execution.

All agents read/write to this shared state during pipeline execution.
Pydantic BaseModel for validation and JSON serialization.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class SharedState(BaseModel):
    """Typed state container for pipeline execution.

    Agents read from this to get upstream results.
    Agents write to this to pass data downstream.
    Pipeline orchestrator creates and manages lifecycle.
    """

    # Pipeline ID
    pipeline_id: str = ""

    # ── Phase 1: Intelligence ──────────────────────────────────────
    product: Optional[dict] = None      # AnalyzeProductOutput
    reviews: Optional[dict] = None      # AnalyzeReviewsOutput
    competitors: Optional[dict] = None  # AnalyzeCompetitorsOutput

    # ── Phase 2: Strategy ──────────────────────────────────────────
    offer: Optional[dict] = None        # GenerateOfferOutput
    pricing: Optional[dict] = None

    # ── Phase 3: Content ───────────────────────────────────────────
    hooks: list[dict] = Field(default_factory=list)
    scripts: list[dict] = Field(default_factory=list)
    thumbnails: list[dict] = Field(default_factory=list)

    # ── Phase 4: Media ─────────────────────────────────────────────
    video: Optional[dict] = None
    avatar: Optional[dict] = None

    # ── Phase 5: Publishing ────────────────────────────────────────
    campaign_id: str = ""
    affiliate_links: dict = Field(default_factory=dict)
    platform_posts: dict = Field(default_factory=dict)

    # ── Metadata ───────────────────────────────────────────────────
    errors: list[dict] = Field(default_factory=list)
    features_used: list[str] = Field(default_factory=list)
    started_at: str = ""
    completed_at: str = ""
    cloud_synced: dict = Field(default_factory=dict)  # {mongodb: bool, notion: bool}

    def mark_error(self, agent: str, error: str) -> None:
        """Record an agent error."""
        self.errors.append({
            "agent": agent,
            "error": error,
            "ts": datetime.utcnow().isoformat(),
        })

    def mark_feature(self, agent: str) -> None:
        """Record a feature as used."""
        if agent not in self.features_used:
            self.features_used.append(agent)

    def duration_seconds(self) -> float:
        """Calculate pipeline duration in seconds."""
        if self.started_at and self.completed_at:
            try:
                start = datetime.fromisoformat(self.started_at)
                end = datetime.fromisoformat(self.completed_at)
                return (end - start).total_seconds()
            except (ValueError, TypeError):
                pass
        return 0.0
