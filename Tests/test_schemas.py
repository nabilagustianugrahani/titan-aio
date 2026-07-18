"""Test Pydantic schemas validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError


class TestSchemas:
    """Test schema validation and defaults."""

    def test_health_output(self):
        from MCP.schemas import HealthOutput
        h = HealthOutput()
        assert h.status == "ok"
        assert h.version == "0.1.0"

    def test_search_product_input_valid(self):
        from MCP.schemas import SearchProductInput
        s = SearchProductInput(query="headphone")
        assert s.query == "headphone"
        assert s.limit == 10

    def test_search_product_input_invalid(self):
        from MCP.schemas import SearchProductInput
        with pytest.raises(ValidationError):
            SearchProductInput(query="")

    def test_analyze_product_output(self):
        from MCP.schemas import AnalyzeProductOutput
        p = AnalyzeProductOutput(
            product_id="p1",
            title="Test",
            price=50000,
            url="https://shopee.co.id/test",
        )
        assert p.product_score == 0.0
        assert p.currency == "IDR"

    def test_analyze_reviews_output_defaults(self):
        from MCP.schemas import AnalyzeReviewsOutput
        r = AnalyzeReviewsOutput(product_id="p1")
        assert r.total_reviews_analyzed == 0
        assert r.pain_points == []

    def test_generate_offer_output(self):
        from MCP.schemas import GenerateOfferOutput
        o = GenerateOfferOutput(
            product_id="p1", primary_angle="Test", value_proposition="VP",
        )
        assert o.primary_angle == "Test"
        assert o.emotional_triggers == []

    def test_create_affiliate_package_input(self):
        from MCP.schemas import CreateAffiliatePackageInput
        c = CreateAffiliatePackageInput(url="https://shopee.co.id/test")
        assert not c.include_video
        assert not c.include_avatar

    def test_get_metrics_output(self):
        from MCP.schemas import GetMetricsOutput
        m = GetMetricsOutput(campaign_id="c1")
        assert m.roi == 0.0

    def test_hook_model(self):
        from MCP.schemas import Hook
        h = Hook(hook="Test hook", type="curiosity", predicted_ctr="high")
        assert h.model_dump()["hook"] == "Test hook"
