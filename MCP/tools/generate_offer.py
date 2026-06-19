"""Generate offer strategy from product, review and competitor analysis."""

from __future__ import annotations

from MCP.schemas import GenerateOfferInput, GenerateOfferOutput


async def generate_offer(input_data: GenerateOfferInput) -> GenerateOfferOutput:
    """Generate optimal offer strategy."""
    pa = input_data.product_analysis
    ra = input_data.review_analysis
    ca = input_data.competitor_analysis

    benefits = ["Kualitas terjamin", "Harga terjangkau"]
    objections = ["Takut barang tidak original"]
    triggers = []

    if ra:
        for b in ra.benefits:
            benefits.append(b.point)
        for o in ra.objections:
            objections.append(o.point)
        triggers = ["FOMO", "Social Proof", "Trust"]

    if ca:
        for h in ca.winning_hooks:
            if h.engagement_est == "high":
                triggers.append("Scarcity")

    return GenerateOfferOutput(
        product_id=input_data.product_id,
        primary_angle="Social Proof + Scarcity",
        value_proposition=f"Produk terbaik di kelasnya dengan harga hanya Rp {pa.price:,.0f}",
        positioning_statement=f"{pa.title} -- solusi #1 untuk kebutuhan Anda",
        target_audience="Pria & Wanita 18-45 tahun, pembeli online aktif",
        emotional_triggers=list(set(triggers)),
        key_benefits_to_highlight=benefits[:5],
        objections_to_address=objections[:3],
        recommended_cta="Beli Sekarang -- Stok Terbatas!",
    )
