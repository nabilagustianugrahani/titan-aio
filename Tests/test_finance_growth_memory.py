"""Tests for upgraded Finance, Growth, and Memory agents."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
class TestFinanceAgent:
    """Test FinanceAgent with DB persistence."""

    async def test_record(self):
        from Services.agents.finance import FinanceAgent
        agent = FinanceAgent()
        result = await agent(
            action="record",
            campaign_id="test-campaign-1",
            revenue=500000,
            ad_spend=100000,
            clicks=200,
            conversions=10,
            platform="tiktok",
        )
        assert result["recorded"] is True
        assert result["revenue"] == 500000
        assert result["ad_spend"] == 100000
        assert result["net_profit"] == 400000
        assert result["roi"] == 4.0
        assert result["data_point_id"]

    async def test_summary(self):
        from Services.agents.finance import FinanceAgent
        agent = FinanceAgent()
        # Record some data first
        await agent(
            action="record",
            campaign_id="test-campaign-summary",
            revenue=200000,
            ad_spend=50000,
            clicks=100,
            conversions=5,
            platform="tiktok",
        )
        result = await agent(action="summary", campaign_id="test-campaign-summary", days=30)
        assert result["total_revenue"] >= 200000
        assert result["total_ad_spend"] >= 50000
        assert result["net_profit"] >= 150000
        assert result["roi"] >= 3.0

    async def test_forecast_insufficient_data(self):
        from Services.agents.finance import FinanceAgent
        agent = FinanceAgent()
        result = await agent(action="forecast", campaign_id="nonexistent-campaign")
        assert result["forecast"] == []
        assert "Insufficient" in result["note"]

    async def test_unknown_action(self):
        from Services.agents.finance import FinanceAgent
        agent = FinanceAgent()
        result = await agent(action="bogus")
        assert "error" in result


@pytest.mark.asyncio
class TestGrowthAgent:
    """Test GrowthAgent with DB persistence."""

    async def test_evaluate_scale(self):
        from Database.connection import async_session_factory
        from Database.models import Campaign
        from Database.repository import Repository
        from Services.agents.growth import GrowthAgent

        # Create a high-ROI campaign
        async with async_session_factory() as session:
            repo = Repository(session, Campaign)
            camp = await repo.create(
                product_id="prod-test",
                name="Scale Test Campaign",
                status="active",
                platform="tiktok",
                budget=200000,
                total_revenue=600000,
                total_spent=100000,
            )
            await session.commit()
            camp_id = camp.id

        agent = GrowthAgent()
        result = await agent(action="evaluate", campaign_id=camp_id)
        assert result["action"] == "scale"
        assert result["roi"] > 2.0
        assert result["budget_change_pct"] > 0

    async def test_evaluate_kill(self):
        from Database.connection import async_session_factory
        from Database.models import Campaign
        from Database.repository import Repository
        from Services.agents.growth import GrowthAgent

        async with async_session_factory() as session:
            repo = Repository(session, Campaign)
            camp = await repo.create(
                product_id="prod-test-kill",
                name="Kill Test Campaign",
                status="active",
                platform="tiktok",
                budget=100000,
                total_revenue=20000,
                total_spent=100000,  # low ROI but spend = 100k (>= kill threshold)
            )
            await session.commit()
            camp_id = camp.id

        agent = GrowthAgent()
        result = await agent(action="evaluate", campaign_id=camp_id)
        assert result["action"] == "kill"
        assert result["roi"] < 0.3

    async def test_evaluate_maintain(self):
        from Database.connection import async_session_factory
        from Database.models import Campaign
        from Database.repository import Repository
        from Services.agents.growth import GrowthAgent

        async with async_session_factory() as session:
            repo = Repository(session, Campaign)
            camp = await repo.create(
                product_id="prod-test-maintain",
                name="Maintain Test",
                status="active",
                platform="tiktok",
                budget=100000,
                total_revenue=150000,
                total_spent=100000,
            )
            await session.commit()
            camp_id = camp.id

        agent = GrowthAgent()
        result = await agent(action="evaluate", campaign_id=camp_id)
        assert result["action"] == "maintain"
        assert 0.3 <= result["roi"] <= 2.0

    async def test_retire(self):
        from Database.connection import async_session_factory
        from Database.models import Campaign, FailedCampaign
        from Database.repository import Repository
        from Services.agents.growth import GrowthAgent

        async with async_session_factory() as session:
            repo = Repository(session, Campaign)
            camp = await repo.create(
                product_id="prod-retire",
                name="Retire Test",
                status="active",
                platform="tiktok",
                total_revenue=10000,
                total_spent=80000,
            )
            await session.commit()
            camp_id = camp.id

        agent = GrowthAgent()
        result = await agent(action="retire", campaign_id=camp_id, reason="Budget exhausted")
        assert result["retired"] is True

        # Verify it was archived
        async with async_session_factory() as session:
            failed_repo = Repository(session, FailedCampaign)
            failures = await failed_repo.find(campaign_id=camp_id)
            assert len(failures) == 1
            assert failures[0].reason == "Budget exhausted"

    async def test_allocate_budget(self):
        from Database.connection import async_session_factory
        from Database.models import Campaign
        from Database.repository import Repository
        from Services.agents.growth import GrowthAgent

        async with async_session_factory() as session:
            repo = Repository(session, Campaign)
            for i in range(3):
                await repo.create(
                    product_id=f"prod-alloc-{i}",
                    name=f"Alloc Test {i}",
                    status="active",
                    platform="tiktok",
                    budget=100000,
                    total_revenue=100000 * (i + 1),
                    total_spent=100000,
                )
            await session.commit()

        agent = GrowthAgent()
        result = await agent(action="allocate", total_budget=300000)
        assert len(result["allocations"]) >= 3
        total_alloc = sum(a["recommended_budget"] for a in result["allocations"])
        assert total_alloc == pytest.approx(300000, abs=100)


@pytest.mark.asyncio
class TestMemoryAgent:
    """Test MemoryAgent with keyword similarity."""

    async def test_store_hook(self):
        from Services.agents.memory import MemoryAgent
        agent = MemoryAgent()
        result = await agent(
            action="store",
            hook="Harga termurah se-Indonesia!",
            hook_type="price_anchor",
            campaign_id="test-campaign",
            ctr=0.065,
        )
        assert result["stored"] is True
        assert result["hook_id"]
        assert result["hook_text"] == "Harga termurah se-Indonesia!"

    async def test_store_empty(self):
        from Services.agents.memory import MemoryAgent
        agent = MemoryAgent()
        result = await agent(action="store", hook="")
        assert result["stored"] is False

    async def test_find_similar_hooks(self):
        from Services.agents.memory import MemoryAgent
        agent = MemoryAgent()
        # Store some hooks first
        await agent(action="store", hook="Garansi resmi 1 tahun!", hook_type="trust_signal", campaign_id="c1")
        await agent(action="store", hook="Cek review jujur di sini!", hook_type="social_proof", campaign_id="c2")

        result = await agent(action="find_similar", query="garansi resmi produk original")
        assert len(result["results"]) > 0
        # Top result should be the garansi hook
        assert "garansi" in result["results"][0]["text"].lower()

    async def test_find_similar_empty_query(self):
        from Services.agents.memory import MemoryAgent
        agent = MemoryAgent()
        result = await agent(action="find_similar", query="")
        assert result["results"] == []

    async def test_learn_pattern(self):
        from Services.agents.memory import MemoryAgent
        agent = MemoryAgent()
        result = await agent(
            action="learn",
            category="hooks",
            pattern="Price anchor hooks outperform curiosity hooks by 40% CTR",
            evidence=["campaign-1 CTR 6.5%", "campaign-2 CTR 4.2%"],
            advice="Lead with price anchors for electronics category",
            confidence=0.75,
        )
        assert result["learned"] is True
        assert result["confidence"] == 0.75

    async def test_find_similar_knowledge(self):
        from Services.agents.memory import MemoryAgent
        agent = MemoryAgent()
        await agent(
            action="learn",
            category="timing",
            pattern="TikTok posts at 7PM WIB get 2x engagement",
            confidence=0.8,
        )
        result = await agent(action="find_similar", query="best posting time tiktok")
        assert len(result["results"]) > 0
        assert result["results"][0]["type"] == "knowledge"

    async def test_keyword_similarity(self):
        from Services.agents.memory import MemoryAgent
        sim = MemoryAgent._keyword_similarity(
            ["harga", "termurah", "indonesia"],
            ["harga", "termurah", "se-indonesia", "promo"],
        )
        assert 0.5 < sim <= 1.0

        sim_zero = MemoryAgent._keyword_similarity(
            ["harga", "termurah"],
            ["beauty", "skincare", "glowing"],
        )
        assert sim_zero == 0.0
