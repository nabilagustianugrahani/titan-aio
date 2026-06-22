"""Test that all modules import correctly."""

from __future__ import annotations



class TestImports:
    """Verify all core modules can be imported."""

    def test_config(self):
        from titan.config import settings
        assert settings.APP_NAME == "TITAN AIO"

    def test_database_connection(self):
        from Database.connection import Base
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
            SearchProductInput, SearchProductOutput,
            AnalyzeProductInput, AnalyzeProductOutput,
            AnalyzeReviewsInput, AnalyzeReviewsOutput,
            AnalyzeCompetitorsInput, AnalyzeCompetitorsOutput,
            GenerateOfferInput, GenerateOfferOutput,
            GenerateHooksInput, GenerateHooksOutput,
            GenerateScriptInput, GenerateScriptOutput,
            GenerateThumbnailInput, GenerateThumbnailOutput,
            GenerateImageInput, GenerateImageOutput,
            GenerateVideoInput,
            CreateAffiliatePackageInput,
        )
        assert HealthOutput().status == "ok"

    def test_mcp_tools(self):
        from MCP.tools.health import health
        from MCP.tools.analyze_product import analyze_product
        from MCP.tools.analyze_reviews import analyze_reviews
        from MCP.tools.analyze_competitors import analyze_competitors
        from MCP.tools.create_affiliate_package import create_affiliate_package
        assert health is not None
        assert analyze_product is not None
        assert analyze_reviews is not None
        assert analyze_competitors is not None
        assert create_affiliate_package is not None

    def test_agents(self):
        from Services.agents.base import BaseAgent
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
