"""MCP tools for content compliance checking and multi-niche campaigns."""

from __future__ import annotations

from MCP.server import mcp

_checker = None


def _get_checker():
    global _checker
    if _checker is None:
        from Services.compliance.content_checker import ContentComplianceChecker

        _checker = ContentComplianceChecker()
    return _checker


@mcp.tool()
async def check_content_compliance(
    content: str,
    platform: str = "tiktok",
    has_affiliate: bool = True,
) -> dict:
    """Check content for platform compliance (char limits, disclosures, banned words)."""
    checker = _get_checker()
    result = checker.check_content(
        content=content, platform=platform, has_affiliate=has_affiliate
    )
    return result.model_dump()


@mcp.tool()
async def create_niche_campaign(
    niche: str,
    name: str,
    platforms: str = "tiktok,instagram",
    budget: float = 0.0,
) -> dict:
    """Create a multi-niche campaign manager entry."""
    from Services.campaign.multi_niche import MultiNicheManager

    mgr = MultiNicheManager()
    plat_list = [p.strip() for p in platforms.split(",") if p.strip()]
    result = await mgr.create_campaign(
        niche=niche, name=name, platforms=plat_list, budget=budget
    )
    return result.model_dump()
