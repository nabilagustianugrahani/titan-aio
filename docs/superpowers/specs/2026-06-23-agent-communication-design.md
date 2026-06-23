# Agent Communication Architecture Design

**Date:** 2026-06-23
**Status:** Approved
**Author:** Claude Code

## Problem Statement

Titan AIO has 35+ agents that need to communicate. Current state:
- Orchestrator passes data sequentially (reliable but rigid)
- MessageBus exists but only used for logging (publish only, no subscribe)
- 3 different state patterns (PipelineState, GraphState, direct passing)
- Agents can't react to events from other agents

**Goal:** Enable agents to share data and react to events while maintaining reliability.

## Architecture: Enhanced MessageBus + SharedState

```
┌─────────────────────────────────────────────────────┐
│                  SharedState (Pydantic)              │
│  product: ProductOutput | reviews: ReviewsOutput    │
│  competitors: CompetitorsOutput | offer: OfferOutput│
│  hooks: list | scripts: list | video: VideoOutput   │
└──────────────┬──────────────────────────────────────┘
               │ read/write
┌──────────────▼──────────────────────────────────────┐
│              MessageBus (Enhanced)                   │
│  publish(event, data) → notify subscribers          │
│  get_latest(event) → poll latest data               │
│  subscribe(event, handler) → reactive agents        │
│  error handling + logging                           │
└──────────────┬──────────────────────────────────────┘
               │ events
┌──────────────▼──────────────────────────────────────┐
│           Pipeline Orchestrator                      │
│  sequential: product → review → competitor → offer   │
│  parallel: review ‖ competitor (asyncio.gather)      │
│  reactive: finance reacts to campaign.created       │
│  resilience: retry + timeout per agent              │
└─────────────────────────────────────────────────────┘
```

## Components

### 1. SharedState (Pydantic BaseModel)

Typed state container that all agents read/write to.

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class SharedState(BaseModel):
    """Typed state container for pipeline execution."""
    
    # Pipeline ID
    pipeline_id: str = ""
    
    # Phase 1: Intelligence
    product: Optional[dict] = None  # AnalyzeProductOutput
    reviews: Optional[dict] = None  # AnalyzeReviewsOutput
    competitors: Optional[dict] = None  # AnalyzeCompetitorsOutput
    
    # Phase 2: Strategy
    offer: Optional[dict] = None  # GenerateOfferOutput
    pricing: Optional[dict] = None
    
    # Phase 3: Content
    hooks: list[dict] = Field(default_factory=list)
    scripts: list[dict] = Field(default_factory=list)
    thumbnails: list[dict] = Field(default_factory=list)
    
    # Phase 4: Media
    video: Optional[dict] = None
    avatar: Optional[dict] = None
    
    # Phase 5: Publishing
    campaign_id: str = ""
    affiliate_links: dict = Field(default_factory=dict)
    platform_posts: dict = Field(default_factory=dict)
    
    # Metadata
    errors: list[dict] = Field(default_factory=list)
    features_used: list[str] = Field(default_factory=list)
    started_at: str = ""
    completed_at: str = ""
```

**Design decisions:**
- Pydantic BaseModel for validation and serialization
- Optional fields — agents only fill what they produce
- Dict types for flexibility (agents return varying structures)
- Metadata fields for tracking and debugging

### 2. Enhanced MessageBus

```python
import logging
import uuid
from datetime import datetime
from typing import Callable, Optional

logger = logging.getLogger(__name__)

class MessageBus:
    """Enhanced event bus with error handling and logging."""
    
    def __init__(self, max_history: int = 1000):
        self._handlers: dict[str, list[Callable]] = {}
        self._latest: dict[str, dict] = {}
        self._history: list[dict] = []
        self._max_history = max_history
    
    def publish(self, event_type: str, data: dict, source: str = "") -> str:
        """Publish event with error handling."""
        eid = str(uuid.uuid4())
        event = {
            "id": eid,
            "type": event_type,
            "data": data,
            "source": source,
            "ts": datetime.utcnow().isoformat(),
        }
        self._latest[event_type] = event
        self._history.append(event)
        
        # Trim history
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history // 2:]
        
        # Notify handlers with error handling
        for handler in self._handlers.get(event_type, []):
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Handler error for {event_type}: {e}")
        
        return eid
    
    def subscribe(self, event_type: str, handler: Callable):
        """Subscribe to event type."""
        self._handlers.setdefault(event_type, []).append(handler)
    
    def get_latest(self, event_type: str) -> Optional[dict]:
        """Get latest event data."""
        e = self._latest.get(event_type)
        return e["data"] if e else None
    
    def get_history(self, event_type: str = "", limit: int = 10) -> list[dict]:
        """Get event history."""
        events = [e for e in self._history if not event_type or e["type"] == event_type]
        return events[-limit:]
    
    def clear(self):
        """Clear all handlers and history."""
        self._handlers.clear()
        self._latest.clear()
        self._history.clear()
```

**Improvements over current:**
1. Error handling per handler (not silent `pass`)
2. Configurable max_history
3. `clear()` method for testing
4. Logger instead of print

### 3. Pipeline Orchestrator

```python
import asyncio
import uuid
from datetime import datetime
from typing import Any, Optional

class Pipeline:
    """Orchestrates agent execution with sequential + parallel flow."""
    
    def __init__(self, agents: dict[str, 'BaseAgent'], bus: 'MessageBus'):
        self.agents = agents
        self.bus = bus
    
    async def run(self, url: str, **kwargs) -> 'SharedState':
        """Run full pipeline: sequential + parallel + reactive."""
        state = SharedState(
            pipeline_id=str(uuid.uuid4()),
            started_at=datetime.utcnow().isoformat()
        )
        
        try:
            # Phase 1: Intelligence (sequential dependency)
            state.product = await self._run_agent("product", state, url=url)
            self.bus.publish("product.analyzed", {
                "product_id": state.product.get("product_id", "")
            }, "Pipeline")
            
            # Phase 2: Analysis (parallel — no dependency)
            reviews_task = self._run_agent("review", state, 
                product_id=state.product.get("product_id", ""))
            competitor_task = self._run_agent("competitor", state, 
                category=state.product.get("category", "umum"))
            
            state.reviews, state.competitors = await asyncio.gather(
                reviews_task, competitor_task
            )
            
            self.bus.publish("reviews.analyzed", {
                "count": state.reviews.get("total_reviews_analyzed", 0)
            }, "Pipeline")
            self.bus.publish("competitors.analyzed", {
                "count": state.competitors.get("competitors_analyzed", 0)
            }, "Pipeline")
            
            # Phase 3: Strategy (needs product + reviews + competitors)
            state.offer = await self._run_agent("offer", state)
            self.bus.publish("offer.created", {
                "angle": state.offer.get("primary_angle", "")
            }, "Pipeline")
            
            # Phase 4: Content (needs offer)
            content_result = await self._run_agent("content", state,
                category=state.product.get("category", "umum"))
            state.hooks = content_result.get("hooks", [])
            state.scripts = content_result.get("scripts", [])
            state.thumbnails = content_result.get("thumbnails", [])
            
            self.bus.publish("content.generated", {
                "hooks_count": len(state.hooks),
                "scripts_count": len(state.scripts)
            }, "Pipeline")
            
            # Phase 5: Media (optional, parallel)
            if kwargs.get("include_video") and state.scripts:
                video_task = self._run_agent("video", state,
                    script=state.scripts[0].get("full_script", ""))
                avatar_result = None
                if kwargs.get("include_avatar"):
                    avatar_task = self._run_agent("avatar", state)
                    avatar_result = await avatar_task
                video_result = await video_task
                state.video = video_result
                state.avatar = avatar_result
            
            # Phase 6: Publishing
            campaign = await self._run_agent("campaign_builder", state)
            state.campaign_id = campaign.get("campaign_id", "")
            
            self.bus.publish("campaign.created", {
                "campaign_id": state.campaign_id
            }, "Pipeline")
            
        except Exception as e:
            state.errors.append({
                "phase": "pipeline",
                "error": str(e),
                "ts": datetime.utcnow().isoformat()
            })
            self.bus.publish("pipeline.error", {"error": str(e)}, "Pipeline")
            raise
        
        state.completed_at = datetime.utcnow().isoformat()
        self.bus.publish("pipeline.complete", {
            "campaign_id": state.campaign_id,
            "duration_seconds": self._calc_duration(state)
        }, "Pipeline")
        
        return state
    
    async def _run_agent(self, name: str, state: 'SharedState', 
                         max_retries: int = 2, timeout: float = 60.0,
                         **kwargs) -> Any:
        """Run single agent with retry + timeout."""
        agent = self.agents.get(name)
        if not agent:
            raise ValueError(f"Agent not found: {name}")
        
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                result = await asyncio.wait_for(
                    agent(state=state, **kwargs),
                    timeout=timeout
                )
                state.features_used.append(name)
                return result
            except asyncio.TimeoutError:
                last_error = f"Timeout after {timeout}s"
                logger.warning(f"Agent {name} timeout (attempt {attempt + 1})")
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Agent {name} error (attempt {attempt + 1}): {e}")
            
            if attempt < max_retries:
                await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
        
        # All retries failed
        error = {
            "agent": name,
            "error": last_error,
            "attempts": max_retries + 1,
            "ts": datetime.utcnow().isoformat()
        }
        state.errors.append(error)
        self.bus.publish("agent.error", error, "Pipeline")
        raise RuntimeError(f"Agent {name} failed after {max_retries + 1} attempts: {last_error}")
    
    def _calc_duration(self, state: 'SharedState') -> float:
        """Calculate pipeline duration in seconds."""
        if state.started_at and state.completed_at:
            start = datetime.fromisoformat(state.started_at)
            end = datetime.fromisoformat(state.completed_at)
            return (end - start).total_seconds()
        return 0.0
```

**Key features:**
1. Sequential + parallel execution via `asyncio.gather`
2. Retry with exponential backoff (max 2 retries)
3. Timeout per agent (default 60s)
4. Error collection in state (not swallowed)
5. MessageBus events at each phase

### 4. Agent Base Class Update

```python
# Services/agents/base.py (updated)

from abc import ABC, abstractmethod
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from Database.connection import async_session_factory


class AgentContext:
    """Context passed to every agent during execution."""
    
    def __init__(self, session: AsyncSession, state: 'SharedState' = None):
        self.session = session
        self.state = state


class BaseAgent(ABC):
    """Abstract base agent with DI support."""
    
    def __init__(self, name: str = "") -> None:
        self.name = name or self.__class__.__name__
    
    async def __call__(self, state: 'SharedState' = None, **kwargs: Any) -> Any:
        """Execute agent with optional shared state."""
        async with async_session_factory() as session:
            ctx = AgentContext(session=session, state=state)
            try:
                return await self.execute(ctx, **kwargs)
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    @abstractmethod
    async def execute(self, ctx: AgentContext, **kwargs: Any) -> Any:
        """Execute the agent's task."""
        ...
```

**Key change:**
- `state` parameter added to `__call__`
- `AgentContext` now includes `state`
- Backward compatible — existing agents work without changes

## Data Flow Example

```
1. Pipeline.run(url="https://shopee.co.id/product/123")
   ↓
2. ProductAgent(state=state, url=url)
   - Reads: state.product (empty)
   - Writes: state.product = {product_id, title, price, ...}
   - Publishes: "product.analyzed"
   ↓
3. asyncio.gather(
     ReviewAgent(state=state, product_id=...),
     CompetitorAgent(state=state, category=...)
   )
   - ReviewAgent reads: state.product
   - ReviewAgent writes: state.reviews
   - CompetitorAgent reads: state.product
   - CompetitorAgent writes: state.competitors
   - Publishes: "reviews.analyzed", "competitors.analyzed"
   ↓
4. OfferAgent(state=state)
   - Reads: state.product, state.reviews, state.competitors
   - Writes: state.offer
   - Publishes: "offer.created"
   ↓
5. ContentAgent(state=state, category=...)
   - Reads: state.offer, state.product
   - Writes: state.hooks, state.scripts, state.thumbnails
   - Publishes: "content.generated"
   ↓
6. VideoAgent(state=state, script=...)
   - Reads: state.scripts[0]
   - Writes: state.video
   - Publishes: "video.generated"
   ↓
7. CampaignBuilder(state=state)
   - Reads: state.product, state.offer, state.hooks
   - Writes: state.campaign_id
   - Publishes: "campaign.created"
   ↓
8. Pipeline returns state
```

## Reactive Agents (Future)

Agents can subscribe to events and react:

```python
# FinanceAgent reacts to campaign.created
class FinanceAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.bus = get_bus()
        self.bus.subscribe("campaign.created", self._on_campaign_created)
    
    async def _on_campaign_created(self, event: dict):
        """React to new campaign."""
        campaign_id = event["data"]["campaign_id"]
        # Auto-track financial metrics
        await self.track_revenue(campaign_id=campaign_id)
```

## Implementation Plan

### Phase 1: Core Infrastructure (1-2 hours)
1. Create `Services/agents/shared_state.py` — SharedState Pydantic model
2. Update `Services/agents/message_bus.py` — Enhanced MessageBus
3. Create `Services/agents/pipeline.py` — Pipeline orchestrator
4. Update `Services/agents/base.py` — Add state parameter

### Phase 2: Agent Updates (2-3 hours)
1. Update `Services/orchestrator.py` — CEOAgent uses Pipeline
2. Update agent `execute()` signatures — Accept state parameter
3. Update MCP tools — Pass state through
4. Test all 35+ agents

### Phase 3: Reactive Agents (1-2 hours)
1. Update FinanceAgent — Subscribe to campaign.created
2. Update GrowthAgent — Subscribe to metrics.updated
3. Update MemoryAgent — Subscribe to content.generated

### Phase 4: Testing (1-2 hours)
1. Unit tests for SharedState
2. Unit tests for MessageBus
3. Unit tests for Pipeline
4. Integration tests for full pipeline

## Migration Strategy

### Backward Compatible
- Existing agents work without changes (state is optional)
- CEOAgent can use old method or new Pipeline
- GraphWorkflow can use SharedState

### Gradual Migration
1. Add SharedState + Pipeline (new code)
2. Update orchestrator to use Pipeline
3. Update agents to accept state
4. Add reactive subscriptions

## Success Criteria

1. **All 35+ agents work** — no breaking changes
2. **Pipeline runs end-to-end** — product URL → campaign created
3. **Parallel execution works** — review ‖ competitor
4. **Error handling works** — retry + timeout + error collection
5. **MessageBus events fire** — product.analyzed, reviews.analyzed, etc.
6. **Reactive agents work** — FinanceAgent reacts to campaign.created
7. **Tests pass** — all existing tests + new tests

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing agents | High | Backward compatible design, optional state |
| Performance overhead | Low | Pydantic is fast, async throughout |
| Memory usage | Low | SharedState is small, history trimmed |
| Debugging complexity | Medium | MessageBus logging, state inspection |

## Future Enhancements

1. **Distributed Pipeline** — Redis-backed MessageBus for multi-process
2. **Visual Pipeline Builder** — GUI to configure agent flow
3. **Pipeline Templates** — Pre-built flows for different product types
4. **Monitoring Dashboard** — Real-time pipeline visualization
5. **Agent Marketplace** — Drop-in agents for common tasks
