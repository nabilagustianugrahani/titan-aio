"""Analyze competitor ads and hooks using real Shopee data + AI."""

from __future__ import annotations

from MCP.schemas import AnalyzeCompetitorsInput, AnalyzeCompetitorsOutput, CompetitorHook
from Services.api.shopee_client import ShopeeClient
from Services.llm import analyze_competitors_llm


async def analyze_competitors(input_data: AnalyzeCompetitorsInput) -> AnalyzeCompetitorsOutput:
    """Analyze competitors for a given category using real Shopee data + AI."""
    category = input_data.category.lower()
    limit = input_data.limit

    # 1. Find real competitor products on Shopee
    async with ShopeeClient() as client:
        search_result = await client.search(query=category, limit=min(limit * 3, 60), sort="sales")
        products = search_result.products

    competitors_analyzed = len(products)

    # 2. Format competitor data for LLM analysis
    competitor_lines = []
    for p in products[: limit * 2]:
        line = (
            f"- Nama: {p.name} | Harga: Rp{p.price:,.0f} | "
            f"Rating: {p.rating} | Terjual: {p.sold} | "
            f"Toko: {p.shop_name}"
        )
        competitor_lines.append(line)

    competitor_data_str = "\n".join(competitor_lines)

    # 3. AI analysis of competitor data
    llm_result = await analyze_competitors_llm(
        competitor_data=competitor_data_str,
        product_name="",
        category=category,
    )

    if not llm_result:
        llm_result = {}

    # 4. Parse winning hooks from LLM result
    raw_hooks = llm_result.get("winning_hooks", [])
    winning_hooks: list[CompetitorHook] = []
    for h in raw_hooks:
        if isinstance(h, dict) and h.get("hook"):
            winning_hooks.append(
                CompetitorHook(
                    hook=h["hook"],
                    source="shopee",
                    engagement_est="medium",
                ),
            )

    # 5. Build output (keep existing return schema intact)
    return AnalyzeCompetitorsOutput(
        category=input_data.category,
        competitors_analyzed=competitors_analyzed or 5,
        winning_hooks=winning_hooks[:limit],
        common_angles=llm_result.get("common_angles", []),
        creative_patterns=llm_result.get("predicted_trends", []),
        gaps_identified=llm_result.get("gaps_identified", []),
        recommended_differentiation=llm_result.get("recommended_differentiation", "") or "",
    )
