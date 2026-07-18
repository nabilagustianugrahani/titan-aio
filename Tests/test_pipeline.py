"""Tests for the new Pipeline architecture: SharedState, MessageBus, Pipeline."""

from __future__ import annotations

import pytest

# ── SharedState Tests ──────────────────────────────────────────────


class TestSharedState:
    def test_default_state(self):
        from Services.agents.shared_state import SharedState
        state = SharedState()
        assert state.pipeline_id == ""
        assert state.product is None
        assert state.reviews is None
        assert state.competitors is None
        assert state.offer is None
        assert state.hooks == []
        assert state.scripts == []
        assert state.video is None
        assert state.campaign_id == ""
        assert state.errors == []
        assert state.features_used == []

    def test_mark_error(self):
        from Services.agents.shared_state import SharedState
        state = SharedState()
        state.mark_error("product", "Connection timeout")
        assert len(state.errors) == 1
        assert state.errors[0]["agent"] == "product"
        assert state.errors[0]["error"] == "Connection timeout"
        assert "ts" in state.errors[0]

    def test_mark_feature(self):
        from Services.agents.shared_state import SharedState
        state = SharedState()
        state.mark_feature("product")
        state.mark_feature("review")
        state.mark_feature("product")  # duplicate — should not add
        assert state.features_used == ["product", "review"]

    def test_duration_seconds(self):
        from Services.agents.shared_state import SharedState
        state = SharedState(
            started_at="2026-06-23T10:00:00",
            completed_at="2026-06-23T10:00:30",
        )
        assert state.duration_seconds() == 30.0

    def test_duration_empty(self):
        from Services.agents.shared_state import SharedState
        state = SharedState()
        assert state.duration_seconds() == 0.0

    def test_json_serialization(self):
        from Services.agents.shared_state import SharedState
        state = SharedState(
            pipeline_id="test-123",
            product={"title": "Test Product", "price": 50000},
            hooks=[{"text": "Hook 1", "style": "bold"}],
        )
        json_str = state.model_dump_json()
        assert "test-123" in json_str
        assert "Test Product" in json_str

    def test_from_dict(self):
        from Services.agents.shared_state import SharedState
        data = {
            "pipeline_id": "from-dict",
            "product": {"title": "Product A"},
            "scripts": [{"script": "test"}],
        }
        state = SharedState(**data)
        assert state.pipeline_id == "from-dict"
        assert state.product["title"] == "Product A"
        assert len(state.scripts) == 1


# ── MessageBus Tests ───────────────────────────────────────────────


class TestMessageBus:
    def setup_method(self):
        from Services.agents.message_bus import MessageBus
        self.bus = MessageBus(max_history=100)

    def test_publish_and_get_latest(self):
        self.bus.publish("test.event", {"value": 42}, source="TestAgent")
        data = self.bus.get_latest("test.event")
        assert data is not None
        assert data["value"] == 42

    def test_publish_overwrites_latest(self):
        self.bus.publish("test.event", {"round": 1})
        self.bus.publish("test.event", {"round": 2})
        data = self.bus.get_latest("test.event")
        assert data["round"] == 2

    def test_get_latest_unknown_event(self):
        assert self.bus.get_latest("nonexistent") is None

    def test_subscribe_and_publish(self):
        received = []
        self.bus.subscribe("test.event", received.append)
        self.bus.publish("test.event", {"x": 1})
        assert len(received) == 1
        assert received[0]["data"]["x"] == 1

    def test_subscribe_multiple_handlers(self):
        results_a, results_b = [], []
        self.bus.subscribe("test.event", results_a.append)
        self.bus.subscribe("test.event", results_b.append)
        self.bus.publish("test.event", {"x": 1})
        assert len(results_a) == 1
        assert len(results_b) == 1

    def test_handler_error_does_not_crash(self):
        def bad_handler(e):
            raise ValueError("oops")

        self.bus.subscribe("test.event", bad_handler)
        # Should not raise
        self.bus.publish("test.event", {"x": 1})
        assert self.bus.get_latest("test.event")["x"] == 1

    def test_get_history(self):
        self.bus.publish("test.event", {"i": 0})
        self.bus.publish("test.event", {"i": 1})
        self.bus.publish("test.event", {"i": 2})
        history = self.bus.get_history("test.event", limit=2)
        assert len(history) == 2
        assert history[0]["data"]["i"] == 1
        assert history[1]["data"]["i"] == 2

    def test_get_history_by_type(self):
        self.bus.publish("type.a", {"x": 1})
        self.bus.publish("type.b", {"x": 2})
        self.bus.publish("type.a", {"x": 3})
        history = self.bus.get_history("type.a")
        assert len(history) == 2

    def test_history_trimming(self):
        bus = __import__("Services.agents.message_bus", fromlist=["MessageBus"]).MessageBus(max_history=10)
        for i in range(15):
            bus.publish("event", {"i": i})
        assert len(bus._history) <= 10

    def test_clear(self):
        self.bus.publish("test.event", {"x": 1})
        self.bus.clear()
        assert self.bus.get_latest("test.event") is None
        assert self.bus.get_history() == []

    def test_unsubscribe(self):
        received = []
        handler = received.append
        self.bus.subscribe("test.event", handler)
        self.bus.publish("test.event", {"x": 1})
        assert len(received) == 1

        self.bus.unsubscribe("test.event", handler)
        self.bus.publish("test.event", {"x": 2})
        assert len(received) == 1  # no new event

    def test_event_has_metadata(self):
        eid = self.bus.publish("test.event", {"x": 1}, source="TestAgent")
        history = self.bus.get_history("test.event")
        assert len(history) == 1
        event = history[0]
        assert event["id"] == eid
        assert event["type"] == "test.event"
        assert event["source"] == "TestAgent"
        assert "ts" in event


# ── Pipeline Tests ─────────────────────────────────────────────────


@pytest.mark.asyncio
class TestPipeline:
    async def test_basic_pipeline(self):
        from Services.agents.base import AgentContext, BaseAgent
        from Services.agents.message_bus import MessageBus
        from Services.agents.pipeline import Pipeline

        class MockProductAgent(BaseAgent):
            async def execute(self, ctx: AgentContext, **kwargs):
                return {"product_id": "p1", "title": "Test Product", "price": 50000}

        class MockCampaignBuilder(BaseAgent):
            async def execute(self, ctx: AgentContext, **kwargs):
                return {"campaign_id": "c1"}

        bus = MessageBus()
        agents = {
            "product": MockProductAgent("product"),
            "campaign_builder": MockCampaignBuilder("campaign_builder"),
        }
        pipeline = Pipeline(agents=agents, bus=bus)

        events = []
        bus.subscribe("product.analyzed", events.append)
        bus.subscribe("campaign.created", events.append)

        state = await pipeline.run(url="https://test.com/product/1")

        assert state.product is not None
        assert state.product["product_id"] == "p1"
        assert state.campaign_id == "c1"
        assert "product" in state.features_used
        assert len(events) == 2

    async def test_parallel_agents(self):
        from Services.agents.base import AgentContext, BaseAgent
        from Services.agents.message_bus import MessageBus
        from Services.agents.pipeline import Pipeline

        class MockProductAgent(BaseAgent):
            async def execute(self, ctx: AgentContext, **kwargs):
                return {"product_id": "p1", "category": "elektronik"}

        class MockReviewAgent(BaseAgent):
            async def execute(self, ctx: AgentContext, **kwargs):
                return {"total_reviews_analyzed": 10}

        class MockCompetitorAgent(BaseAgent):
            async def execute(self, ctx: AgentContext, **kwargs):
                return {"competitors_analyzed": 5}

        bus = MessageBus()
        agents = {
            "product": MockProductAgent("product"),
            "review": MockReviewAgent("review"),
            "competitor": MockCompetitorAgent("competitor"),
        }
        pipeline = Pipeline(agents=agents, bus=bus)

        state = await pipeline.run(url="https://test.com/product/1")

        assert state.product["product_id"] == "p1"
        assert state.reviews["total_reviews_analyzed"] == 10
        assert state.competitors["competitors_analyzed"] == 5

    async def test_agent_timeout(self):
        import asyncio

        from Services.agents.base import AgentContext, BaseAgent
        from Services.agents.message_bus import MessageBus
        from Services.agents.pipeline import Pipeline

        class SlowAgent(BaseAgent):
            async def execute(self, ctx: AgentContext, **kwargs):
                await asyncio.sleep(10)
                return {}

        bus = MessageBus()
        agents = {"product": SlowAgent("product")}
        pipeline = Pipeline(agents=agents, bus=bus, timeout=0.1)

        with pytest.raises(RuntimeError, match="failed after"):
            await pipeline.run(url="https://test.com")

    async def test_agent_retry(self):
        from Services.agents.base import AgentContext, BaseAgent
        from Services.agents.message_bus import MessageBus
        from Services.agents.pipeline import Pipeline

        call_count = 0

        class FlakyAgent(BaseAgent):
            async def execute(self, ctx: AgentContext, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count < 3:
                    raise ValueError(f"Attempt {call_count} failed")
                return {"product_id": "p1", "title": "Recovered"}

        bus = MessageBus()
        agents = {"product": FlakyAgent("product")}
        pipeline = Pipeline(agents=agents, bus=bus, max_retries=3)

        state = await pipeline.run(url="https://test.com")
        assert call_count == 3
        assert state.product["product_id"] == "p1"

    async def test_agent_error_collection(self):
        from Services.agents.base import AgentContext, BaseAgent
        from Services.agents.message_bus import MessageBus
        from Services.agents.pipeline import Pipeline

        class FailAgent(BaseAgent):
            async def execute(self, ctx: AgentContext, **kwargs):
                raise ValueError("Agent failed")

        bus = MessageBus()
        agents = {"product": FailAgent("product")}
        pipeline = Pipeline(agents=agents, bus=bus, max_retries=0)

        with pytest.raises(RuntimeError):
            await pipeline.run(url="https://test.com")

        # Error should be in history
        errors = bus.get_history("agent.error")
        assert len(errors) == 1
        assert errors[0]["data"]["agent"] == "product"

    async def test_missing_agent(self):
        from Services.agents.message_bus import MessageBus
        from Services.agents.pipeline import Pipeline

        bus = MessageBus()
        agents = {}  # empty
        pipeline = Pipeline(agents=agents, bus=bus)

        with pytest.raises(ValueError, match="Agent not found"):
            await pipeline.run(url="https://test.com")

    async def test_events_published(self):
        from Services.agents.base import AgentContext, BaseAgent
        from Services.agents.message_bus import MessageBus
        from Services.agents.pipeline import Pipeline

        class MockAgent(BaseAgent):
            async def execute(self, ctx: AgentContext, **kwargs):
                return {"product_id": "p1", "category": "test"}

        bus = MessageBus()
        agents = {"product": MockAgent("product")}
        pipeline = Pipeline(agents=agents, bus=bus)

        events = []
        bus.subscribe("product.analyzed", events.append)

        await pipeline.run(url="https://test.com")

        assert len(events) == 1
        assert events[0]["data"]["product_id"] == "p1"

    async def test_pipeline_timing(self):
        from Services.agents.base import AgentContext, BaseAgent
        from Services.agents.message_bus import MessageBus
        from Services.agents.pipeline import Pipeline

        class QuickAgent(BaseAgent):
            async def execute(self, ctx: AgentContext, **kwargs):
                return {"product_id": "p1"}

        bus = MessageBus()
        agents = {"product": QuickAgent("product")}
        pipeline = Pipeline(agents=agents, bus=bus)

        state = await pipeline.run(url="https://test.com")

        assert state.started_at != ""
        assert state.completed_at != ""
        assert state.duration_seconds() >= 0


# ── Integration: Pipeline + Real Agents ────────────────────────────


@pytest.mark.asyncio
class TestPipelineIntegration:
    async def test_product_agent_in_pipeline(self):
        from Services.agents.campaign_builder import CampaignBuilder
        from Services.agents.message_bus import MessageBus
        from Services.agents.pipeline import Pipeline
        from Services.agents.product import ProductAgent

        bus = MessageBus()
        agents = {
            "product": ProductAgent("product"),
            "campaign_builder": CampaignBuilder("campaign_builder"),
        }
        pipeline = Pipeline(agents=agents, bus=bus)

        state = await pipeline.run(url="https://shopee.co.id/test-product-abc12345")

        assert state.product is not None
        assert state.product.get("product_id")
        assert state.product.get("price", 0) > 0
        assert state.campaign_id != ""
        assert "product" in state.features_used
        assert "campaign_builder" in state.features_used

    async def test_full_core_pipeline(self):
        from Services.agents.campaign_builder import CampaignBuilder
        from Services.agents.competitor import CompetitorAgent
        from Services.agents.content import ContentAgent
        from Services.agents.message_bus import MessageBus
        from Services.agents.offer import OfferAgent
        from Services.agents.pipeline import Pipeline
        from Services.agents.product import ProductAgent
        from Services.agents.review import ReviewAgent

        bus = MessageBus()
        agents = {
            "product": ProductAgent("product"),
            "review": ReviewAgent("review"),
            "competitor": CompetitorAgent("competitor"),
            "offer": OfferAgent("offer"),
            "content": ContentAgent("content"),
            "campaign_builder": CampaignBuilder("campaign_builder"),
        }
        pipeline = Pipeline(agents=agents, bus=bus)

        state = await pipeline.run(url="https://shopee.co.id/test-full-pipeline-abc")

        # All phases completed
        assert state.product is not None
        assert state.reviews is not None
        assert state.competitors is not None
        assert state.offer is not None
        assert state.campaign_id != ""

        # Features tracked
        assert "product" in state.features_used
        assert "review" in state.features_used
        assert "competitor" in state.features_used
        assert "offer" in state.features_used
        assert "content" in state.features_used
        assert "campaign_builder" in state.features_used

        # MessageBus events
        assert bus.get_latest("product.analyzed") is not None
        assert bus.get_latest("campaign.created") is not None
