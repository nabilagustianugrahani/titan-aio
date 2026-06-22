"""A/B Stats Engine — MCP tool wrappers for statistical significance testing."""

from __future__ import annotations

from pydantic import BaseModel, Field

from Services.analytics.ab_stats import (
    ABTest,
    ABTestCreate,
    create_test,
    delete_test,
    get_test,
    list_tests,
    promote_winner,
    required_sample_size,
    update_variant,
)


# ── Input models ────────────────────────────────────────────────────


class CreateABTestInput(BaseModel):
    """Input for creating an A/B test."""

    test_name: str = Field(description="Name for the A/B test")
    variants: str = Field(description="Comma-separated variant descriptions")
    niche: str = Field(default="general", description="Product/content niche")
    platform: str = Field(default="tiktok", description="Target platform")


class UpdateABTestInput(BaseModel):
    """Input for updating A/B test variant metrics."""

    test_id: str = Field(description="A/B test ID")
    variant_id: str = Field(description="Variant ID to update")
    impressions: int = Field(default=0, ge=0, description="New impressions to add")
    clicks: int = Field(default=0, ge=0, description="New clicks to add")
    conversions: int = Field(default=0, ge=0, description="New conversions to add")


class GetABResultsInput(BaseModel):
    """Input for getting A/B test results."""

    test_id: str = Field(description="A/B test ID")


class SampleSizeInput(BaseModel):
    """Input for sample size calculation."""

    baseline_rate: float = Field(
        description="Current conversion/click rate (0-1)"
    )
    mde: float = Field(default=0.1, description="Minimum detectable effect (fraction)")
    power: float = Field(default=0.8, description="Statistical power")


class ListABTestsInput(BaseModel):
    """Input for listing A/B tests."""

    status_filter: str = Field(
        default="", description="Filter by status: running/significant/inconclusive"
    )


# ── Tool functions ──────────────────────────────────────────────────


async def create_ab_test(
    test_name: str,
    variants: str,
    niche: str = "general",
    platform: str = "tiktok",
) -> dict:
    """Create an A/B test with multiple content variants.

    Args:
        test_name: Name for the test.
        variants: Comma-separated variant descriptions.
        niche: Product/content niche.
        platform: Target platform.

    Returns:
        Test details with variant IDs for tracking.
    """
    variant_list = [v.strip() for v in variants.split(",") if v.strip()]

    if len(variant_list) < 2:
        return {
            "error": "Need at least 2 variants. Provide comma-separated descriptions.",
            "status": "failed",
        }

    if len(variant_list) > 6:
        return {
            "error": "Maximum 6 variants per test.",
            "status": "failed",
        }

    input_data = ABTestCreate(
        test_name=test_name,
        variants=variant_list,
        niche=niche,
        platform=platform,
    )
    test = create_test(input_data)
    return _test_to_dict(test)


async def update_ab_test(
    test_id: str,
    variant_id: str,
    impressions: int = 0,
    clicks: int = 0,
    conversions: int = 0,
) -> dict:
    """Update A/B test metrics for a variant.

    Call this repeatedly as data comes in. Metrics accumulate.

    Args:
        test_id: The A/B test ID.
        variant_id: The variant ID to update.
        impressions: New impressions to add.
        clicks: New clicks to add.
        conversions: New conversions to add.

    Returns:
        Updated test state with significance results.
    """
    test = update_variant(
        test_id=test_id,
        variant_id=variant_id,
        impressions=impressions,
        clicks=clicks,
        conversions=conversions,
    )

    if test is None:
        return {
            "error": f"Test '{test_id}' or variant '{variant_id}' not found.",
            "status": "failed",
        }

    return _test_to_dict(test)


async def get_ab_results(test_id: str) -> dict:
    """Get A/B test results with statistical significance.

    Args:
        test_id: The A/B test ID.

    Returns:
        Full test results including winner, confidence, and recommendations.
    """
    test = get_test(test_id)

    if test is None:
        return {
            "error": f"Test '{test_id}' not found.",
            "status": "failed",
        }

    return _test_to_dict(test)


async def list_ab_tests(status_filter: str = "") -> dict:
    """List all A/B tests with optional status filter.

    Args:
        status_filter: Filter by 'running', 'significant', or 'inconclusive'. Empty = all.

    Returns:
        List of test summaries.
    """
    tests = list_tests(status_filter)
    return {
        "total": len(tests),
        "tests": [_test_to_dict(t) for t in tests],
    }


async def promote_ab_winner(test_id: str) -> dict:
    """Promote the winning variant and retire losers.

    Args:
        test_id: The A/B test ID (must have a determined winner).

    Returns:
        Updated test with promotion status.
    """
    test = promote_winner(test_id)

    if test is None:
        return {
            "error": f"Test '{test_id}' not found or no winner determined yet.",
            "status": "failed",
        }

    return _test_to_dict(test)


async def delete_ab_test(test_id: str) -> dict:
    """Delete an A/B test.

    Args:
        test_id: The A/B test ID to delete.

    Returns:
        Deletion confirmation.
    """
    removed = delete_test(test_id)
    if not removed:
        return {
            "error": f"Test '{test_id}' not found.",
            "status": "failed",
        }
    return {"test_id": test_id, "status": "deleted"}


async def calculate_sample_size(
    baseline_rate: float,
    mde: float = 0.1,
    power: float = 0.8,
) -> dict:
    """Calculate required sample size for an A/B test.

    Args:
        baseline_rate: Current conversion/click rate (0-1, e.g., 0.05 for 5%).
        mde: Minimum detectable effect as fraction of baseline (0.1 = 10% lift).
        power: Statistical power (default 0.8 = 80%).

    Returns:
        Minimum and recommended sample sizes per variant.
    """
    if baseline_rate <= 0.0 or baseline_rate >= 1.0:
        return {"error": "baseline_rate must be between 0 and 1 (exclusive)", "status": "failed"}
    if mde <= 0.0:
        return {"error": "mde must be positive", "status": "failed"}

    result = required_sample_size(
        baseline_rate=baseline_rate,
        mde=mde,
        power=power,
    )
    return {
        "minimum_per_variant": result.minimum_sample_per_variant,
        "recommended_per_variant": result.recommended_sample_per_variant,
        "power": result.power,
        "significance_level": result.significance_level,
        "mde": result.mde,
        "note": (
            f"To detect a {mde*100:.0f}% lift from {baseline_rate*100:.1f}% baseline, "
            f"you need at least {result.minimum_sample_per_variant} impressions per variant "
            f"({result.recommended_sample_per_variant} recommended with buffer)."
        ),
    }


# ── Helpers ─────────────────────────────────────────────────────────


def _test_to_dict(test: ABTest) -> dict:
    """Serialize test to a clean dict."""
    d = test.model_dump()
    d["status"] = test.status
    d["confidence"] = test.confidence
    d["winner"] = test.winner
    d["lift"] = test.lift
    d["recommendation"] = test.recommendation
    d["total_impressions"] = test.total_impressions
    d["total_clicks"] = test.total_clicks
    return d
