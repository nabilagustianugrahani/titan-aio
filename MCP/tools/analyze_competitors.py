"""Analyze competitor ads and hooks."""

from __future__ import annotations

from MCP.schemas import AnalyzeCompetitorsInput, AnalyzeCompetitorsOutput, CompetitorHook


_FAKE_COMPETITOR_DATA = {
    "elektronik": {
        "hooks": [
            CompetitorHook(hook="Harga termurah se-Indonesia!", source="shopee_ads", engagement_est="high"),
            CompetitorHook(hook="Garansi resmi 1 tahun, jangan khawatir!", source="tokopedia_ads", engagement_est="high"),
            CompetitorHook(hook="Cuma hari ini! Diskon 50% + gratis ongkir", source="instagram_ads", engagement_est="high"),
            CompetitorHook(hook="Review: 4.9 bintang dari 10rb pembeli", source="shopee_ads", engagement_est="medium"),
            CompetitorHook(hook="Sudah terjual 50rb+, bukti kualitas!", source="tokopedia_ads", engagement_est="medium"),
        ],
        "angles": ["harga murah", "garansi resmi", "diskon terbatas", "bukti sosial", "gratis ongkir"],
        "creatives": ["produk shot dengan background putih", "before-after perbandingan", "influencer endorsment"],
    }
}


async def analyze_competitors(input_data: AnalyzeCompetitorsInput) -> AnalyzeCompetitorsOutput:
    """Analyze competitors for a given category."""
    cat_data = _FAKE_COMPETITOR_DATA.get(input_data.category.lower(), _FAKE_COMPETITOR_DATA["elektronik"])

    return AnalyzeCompetitorsOutput(
        category=input_data.category,
        competitors_analyzed=5,
        winning_hooks=cat_data["hooks"][:input_data.limit],
        common_angles=cat_data["angles"],
        creative_patterns=cat_data["creatives"],
        gaps_identified=[
            "Belum ada yang pakai angle testimonial pengguna",
            "Video UGC masih jarang di kategori ini",
        ],
        recommended_differentiation="Fokus pada storytelling pengguna nyata dibanding spec sheet.",
    )
