"""Test that all modules import correctly."""

from __future__ import annotations

import pytest


class TestImports:
    """Verify all core modules can be imported."""

    def test_config(self):
        from titan.config import settings
        assert settings.APP_NAME == "TITAN AIO"

    def test_database_connection(self):
        from Database.connection import Base, get_session, init_db, close_db
        assert Base is not None

    def test_database_models(self):
        from Database.models import Product, Review, Campaign
        assert Product.__tablename__ == "products"
        assert Review.__tablename__ == "reviews"
        assert Campaign.__tablename__ == "campaigns"

    def test_repository(self):
        from Database.repository import Repository
        assert Repository is not None

    def test_schemas(self):
        from MCP.schemas import (
            HealthOutput,
            SearchProductOutput,
            AnalyzeProductOutput,
            AnalyzeReviewsOutput,
            AnalyzeCompetitorsOutput,
            GenerateOfferOutput,
            GenerateHooksOutput,
            GenerateScriptOutput,
            GenerateThumbnailOutput,
            GenerateImageOutput,
            AffiliatePackageOutput,
        )
        assert HealthOutput().status == "ok"

    def test_mcp_tools(self):
        from MCP.tools.health import health
        from MCP.tools.search_product import search_product
        from MCP.tools.analyze_product import analyze_product
        from MCP.tools.analyze_reviews import analyze_reviews
        from MCP.tools.analyze_competitors import analyze_competitors
        from MCP.tools.generate_offer import generate_offer
        from MCP.tools.generate_hooks import generate_hooks
        from MCP.tools.generate_script import generate_script
        from MCP.tools.generate_thumbnail import generate_thumbnail
        from MCP.tools.generate_image import generate_image
        assert health is not None

    def test_agents(self):
        from Services.agents.base import BaseAgent, AgentContext
        from Services.agents.product import ProductAgent
        from Services.agents.review import ReviewAgent
        from Services.agents.content import ContentAgent
        assert BaseAgent is not None

    def test_workers(self):
        """Workers have been removed. Kaggle CLI handles this directly."""
        pass

    def test_vector_store(self):
        from Services.memory.vector_store import VectorStore
        assert VectorStore is not None

    def test_ceo_orchestrator(self):
        from Services.orchestrator import CEOAgent
        assert CEOAgent is not None
