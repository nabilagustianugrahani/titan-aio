"""Pipeline — orchestrates agent execution with sequential + parallel flow.

Features:
- Sequential dependencies (product → review → competitor → offer → content)
- Parallel fan-out (review ‖ competitor)
- Retry with exponential backoff
- Timeout per agent
- Error collection (not swallowed)
- MessageBus events at each phase

Usage:
    from Services.agents.pipeline import Pipeline
    from Services.agents.message_bus import get_bus
    from Services.agents.shared_state import SharedState

    agents = {
        "product": ProductAgent(),
        "review": ReviewAgent(),
        "competitor": CompetitorAgent(),
        "offer": OfferAgent(),
        "content": ContentAgent(),
    }
    pipeline = Pipeline(agents=agents, bus=get_bus())
    state = await pipeline.run(url="https://shopee.co.id/product/123")
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any

from Services.agents.base import BaseAgent
from Services.agents.message_bus import MessageBus
from Services.agents.shared_state import SharedState
from MCP.schemas import (
    AnalyzeCompetitorsOutput,
    AnalyzeProductOutput,
    AnalyzeReviewsOutput,
)

logger = logging.getLogger(__name__)


def _safe_get(obj, key: str, default=None):
    """Get attribute/key from object that might be dict or Pydantic model."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _to_dicts(items) -> list[dict]:
    """Convert Pydantic model, list, or dict to list[dict].

    Handles:
    - GenerateHooksOutput(hooks=[Hook(...)]) → list of hook dicts
    - GenerateScriptOutput(scripts=[Script(...)]) → list of script dicts
    - list[dict] → passthrough
    - list[Pydantic] → convert each to dict
    """
    if items is None:
        return []
    # Pydantic model with a nested list attribute
    if hasattr(items, "hooks"):
        return [h.model_dump() if hasattr(h, "model_dump") else h for h in items.hooks]
    if hasattr(items, "scripts"):
        return [s.model_dump() if hasattr(s, "model_dump") else s for s in items.scripts]
    # Already a list
    if isinstance(items, list):
        result = []
        for item in items:
            if hasattr(item, "model_dump"):
                result.append(item.model_dump())
            elif isinstance(item, dict):
                result.append(item)
            else:
                result.append({"value": str(item)})
        return result
    if isinstance(items, dict):
        return [items]
    return []

# Default configuration
DEFAULT_MAX_RETRIES = 2
DEFAULT_TIMEOUT = 60.0
DEFAULT_RETRY_DELAY = 1.0


class Pipeline:
    """Orchestrates agent execution with sequential + parallel flow."""

    def __init__(
        self,
        agents: dict[str, BaseAgent],
        bus: MessageBus,
        max_retries: int = DEFAULT_MAX_RETRIES,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self.agents = agents
        self.bus = bus
        self.max_retries = max_retries
        self.timeout = timeout

    async def run(self, url: str, **kwargs) -> SharedState:
        """Run full pipeline: sequential + parallel + reactive.

        Args:
            url: Product URL to analyze
            **kwargs: Additional options (include_video, include_avatar, etc.)

        Returns:
            SharedState with all results
        """
        state = SharedState(
            pipeline_id=str(uuid.uuid4()),
            started_at=datetime.utcnow().isoformat(),
        )

        try:
            # ── Phase 1: Intelligence ──────────────────────────────
            await self._run_intelligence(state, url)

            # ── Phase 2: Strategy ──────────────────────────────────
            await self._run_strategy(state)

            # ── Phase 3: Content ───────────────────────────────────
            await self._run_content(state)

            # ── Phase 4: Media (optional) ──────────────────────────
            await self._run_media(state, **kwargs)

            # ── Phase 5: Publishing ────────────────────────────────
            await self._run_publishing(state)

            # ── Phase 6: Cloud Sync (optional, non-blocking) ──
            await self._sync_cloud(state)

        except Exception as e:
            state.errors.append({
                "phase": "pipeline",
                "error": str(e),
                "ts": datetime.utcnow().isoformat(),
            })
            self.bus.publish("pipeline.error", {"error": str(e)}, "Pipeline")
            raise

        state.completed_at = datetime.utcnow().isoformat()
        self.bus.publish(
            "pipeline.complete",
            {
                "campaign_id": state.campaign_id,
                "duration_seconds": state.duration_seconds(),
                "features_used": state.features_used,
            },
            "Pipeline",
        )

        return state

    # ── Phase Runners ──────────────────────────────────────────────

    async def _run_intelligence(self, state: SharedState, url: str) -> None:
        """Phase 1: Product analysis, reviews, competitors."""
        # Product (must run first — others depend on it)
        state.product = await self._run_agent("product", state, url=url)
        self.bus.publish(
            "product.analyzed",
            {"product_id": _safe_get(state.product, "product_id", "")},
            "Pipeline",
        )

        # Reviews + Competitors (parallel — no dependency between them)
        if "review" in self.agents and "competitor" in self.agents:
            reviews_task = self._run_agent(
                "review", state,
                product_id=_safe_get(state.product, "product_id", ""),
            )
            competitor_task = self._run_agent(
                "competitor", state,
                category=_safe_get(state.product, "category") or "umum",
            )
            state.reviews, state.competitors = await asyncio.gather(
                reviews_task, competitor_task,
            )
            self.bus.publish(
                "reviews.analyzed",
                {"count": _safe_get(state.reviews, "total_reviews_analyzed", 0)},
                "Pipeline",
            )
            self.bus.publish(
                "competitors.analyzed",
                {"count": _safe_get(state.competitors, "competitors_analyzed", 0)},
                "Pipeline",
            )
        elif "review" in self.agents:
            state.reviews = await self._run_agent(
                "review", state,
                product_id=_safe_get(state.product, "product_id", ""),
            )
        elif "competitor" in self.agents:
            state.competitors = await self._run_agent(
                "competitor", state,
                category=_safe_get(state.product, "category") or "umum",
            )

    async def _run_strategy(self, state: SharedState) -> None:
        """Phase 2: Offer strategy (needs product + reviews + competitors)."""
        if "offer" not in self.agents:
            return

        # Convert dicts to Pydantic models (OfferAgent expects typed models)
        product = state.product
        if isinstance(product, dict):
            product = AnalyzeProductOutput(**product)

        reviews = state.reviews
        if isinstance(reviews, dict):
            reviews = AnalyzeReviewsOutput(**reviews)

        competitors = state.competitors
        if isinstance(competitors, dict):
            competitors = AnalyzeCompetitorsOutput(**competitors)

        state.offer = await self._run_agent(
            "offer", state,
            product=product,
            reviews=reviews,
            competitors=competitors,
        )
        self.bus.publish(
            "offer.created",
            {"angle": _safe_get(state.offer, "primary_angle", "") if state.offer else ""},
            "Pipeline",
        )

    async def _run_content(self, state: SharedState) -> None:
        """Phase 3: Hooks, scripts, thumbnails (needs offer)."""
        if "content" not in self.agents:
            return

        content_result = await self._run_agent(
            "content", state,
            product_id=_safe_get(state.product, "product_id", ""),
            offer_strategy=state.offer,
            category=(_safe_get(state.product, "category") if state.product else None) or "umum",
            title=_safe_get(state.product, "title", "Product"),
        )
        if content_result:
            # ContentAgent may return Pydantic objects — convert to list[dict]
            state.hooks = _to_dicts(_safe_get(content_result, "hooks", []))
            state.scripts = _to_dicts(_safe_get(content_result, "scripts", []))
            # ContentAgent returns "thumbnail" (singular GenerateThumbnailOutput)
            # or "thumbnails" (list) — handle both
            thumb = _safe_get(content_result, "thumbnail") or _safe_get(content_result, "thumbnails")
            if thumb:
                state.thumbnails = _to_dicts(thumb) if isinstance(thumb, (list, dict)) else [{"thumbnail": thumb.model_dump() if hasattr(thumb, "model_dump") else thumb}]

        self.bus.publish(
            "content.generated",
            {
                "hooks_count": len(state.hooks),
                "scripts_count": len(state.scripts),
            },
            "Pipeline",
        )

    async def _run_media(self, state: SharedState, **kwargs) -> None:
        """Phase 4: Video + Avatar (optional, parallel)."""
        include_video = kwargs.get("include_video", False)
        include_avatar = kwargs.get("include_avatar", False)

        if not include_video and not include_avatar:
            return

        tasks = {}
        if include_video and state.scripts and "video" in self.agents:
            script = _safe_get(state.scripts[0], "full_script", "") if state.scripts else ""
            tasks["video"] = self._run_agent("video", state, script=script)

        if include_avatar and "avatar" in self.agents:
            tasks["avatar"] = self._run_agent("avatar", state)

        if tasks:
            results = await asyncio.gather(
                *tasks.values(), return_exceptions=True,
            )
            for key, result in zip(tasks.keys(), results):
                if isinstance(result, Exception):
                    state.mark_error(f"media.{key}", str(result))
                else:
                    setattr(state, key, result)

    async def _run_publishing(self, state: SharedState) -> None:
        """Phase 5: Campaign creation."""
        if "campaign_builder" not in self.agents:
            return

        campaign = await self._run_agent("campaign_builder", state)
        state.campaign_id = _safe_get(campaign, "campaign_id", "") if campaign else ""

        self.bus.publish(
            "campaign.created",
            {"campaign_id": state.campaign_id},
            "Pipeline",
        )

    async def _sync_cloud(self, state: SharedState) -> None:
        """Phase 6: Sync to MongoDB (analytics) + Notion (dashboard).

        Non-blocking: failures are logged, not raised.
        MongoDB stores time-series analytics for querying.
        Notion pushes campaign + knowledge for dashboard monitoring.
        """
        # ── MongoDB: store campaign analytics ──
        try:
            from titan.config import settings
            if settings.MONGODB_URI:
                from Services.mongodb.client import MongoDBClient
                mongo = MongoDBClient.get_instance()
                doc = {
                    "pipeline_id": state.pipeline_id,
                    "campaign_id": state.campaign_id,
                    "product": state.product,
                    "hooks_count": len(state.hooks),
                    "scripts_count": len(state.scripts),
                    "features_used": state.features_used,
                    "errors": state.errors,
                    "started_at": state.started_at,
                    "completed_at": state.completed_at,
                    "duration_seconds": state.duration_seconds(),
                }
                await mongo.insert_one_async("pipeline_runs", doc)
                state.cloud_synced["mongodb"] = True
                self.bus.publish("cloud.mongodb.synced", {"pipeline_id": state.pipeline_id}, "Pipeline")
        except Exception as e:
            logger.warning(f"MongoDB sync failed: {e}")

        # ── Notion: push campaign + knowledge to dashboard ──
        try:
            from titan.config import settings
            if settings.NOTION_TOKEN and settings.NOTION_CAMPAIGN_DB:
                from Services.notion.sync import NotionDashboard
                dashboard = NotionDashboard()
                # Build a minimal AffiliatePackageOutput for Notion
                product_title = _safe_get(state.product, "title", "Unknown") if state.product else "Unknown"
                product_url = _safe_get(state.product, "url", "") if state.product else ""
                product_price = _safe_get(state.product, "price", 0) if state.product else 0

                from MCP.schemas import (
                    AffiliatePackageOutput, AnalyzeProductOutput,
                    AnalyzeReviewsOutput, AnalyzeCompetitorsOutput,
                    GenerateOfferOutput, GenerateHooksOutput,
                    GenerateScriptOutput, GenerateThumbnailOutput,
                    GenerateImageOutput,
                )
                package = AffiliatePackageOutput(
                    product=AnalyzeProductOutput(
                        product_id=state.campaign_id,
                        title=product_title,
                        price=product_price,
                        url=product_url,
                    ),
                    review_summary=AnalyzeReviewsOutput(
                        product_id=state.campaign_id,
                        total_reviews_analyzed=0,
                        average_rating=0,
                        sentiment_summary="",
                        benefits=[], objections=[], pain_points=[], top_quotes=[],
                    ),
                    competitor_analysis=AnalyzeCompetitorsOutput(
                        competitors_analyzed=0, competitors=[],
                        winning_hooks=[], market_gaps=[], recommendations=[],
                    ),
                    offer_strategy=GenerateOfferOutput(
                        product_id=state.campaign_id,
                        primary_angle="",
                        value_proposition="",
                    ),
                    hooks=GenerateHooksOutput(product_id=state.campaign_id),
                    scripts=GenerateScriptOutput(product_id=state.campaign_id),
                    thumbnail=GenerateThumbnailOutput(product_id=state.campaign_id),
                    image=GenerateImageOutput(image_url=""),
                )
                package.campaign_id = state.campaign_id
                result = dashboard.push_affiliate_package(package)
                state.cloud_synced["notion"] = True
                self.bus.publish("cloud.notion.synced", result, "Pipeline")
        except Exception as e:
            logger.warning(f"Notion sync failed: {e}")

    # ── Agent Runner ───────────────────────────────────────────────

    async def _run_agent(
        self,
        name: str,
        state: SharedState,
        max_retries: int | None = None,
        timeout: float | None = None,
        **kwargs,
    ) -> Any:
        """Run single agent with retry + timeout.

        Args:
            name: Agent name (key in self.agents)
            state: SharedState to pass to agent
            max_retries: Override default retry count
            timeout: Override default timeout
            **kwargs: Additional arguments to pass to agent

        Returns:
            Agent result

        Raises:
            RuntimeError: If agent fails after all retries
        """
        agent = self.agents.get(name)
        if not agent:
            raise ValueError(f"Agent not found: {name}")

        retries = max_retries if max_retries is not None else self.max_retries
        tout = timeout if timeout is not None else self.timeout
        last_error = None

        for attempt in range(retries + 1):
            try:
                result = await asyncio.wait_for(
                    agent(state=state, **kwargs),
                    timeout=tout,
                )
                state.mark_feature(name)
                return result
            except asyncio.TimeoutError:
                last_error = f"Timeout after {tout}s"
                logger.warning(
                    f"Agent {name} timeout (attempt {attempt + 1}/{retries + 1})"
                )
            except Exception as e:
                last_error = str(e)
                logger.warning(
                    f"Agent {name} error (attempt {attempt + 1}/{retries + 1}): {e}"
                )

            # Exponential backoff before retry
            if attempt < retries:
                delay = DEFAULT_RETRY_DELAY * (attempt + 1)
                await asyncio.sleep(delay)

        # All retries failed
        error = {
            "agent": name,
            "error": last_error,
            "attempts": retries + 1,
            "ts": datetime.utcnow().isoformat(),
        }
        state.errors.append(error)
        self.bus.publish("agent.error", error, "Pipeline")
        raise RuntimeError(
            f"Agent {name} failed after {retries + 1} attempts: {last_error}"
        )
