"""CommissionHunter Agent — find products with HIGHEST affiliate commission.

Strategi:
1. Cari produk trending / bestseller di Shopee, Tokopedia, TikTok Shop
2. Estimasi komisi dari harga × rate (umumnya 5-20%)
3. Hitung profit potential = komisi × estimasi penjualan
4. Ranking dari yang paling menguntungkan
5. Bonus: cek komisi riil dari program afiliasi (kalau API tersedia)

Commission rate estimates by category:
  Elektronik    → 1-5%   (margin tipis)
  Fashion       → 10-20% (margin gede)
  Kesehatan     → 10-25% (margin paling gede)
  Kecantikan    → 15-30% (tertinggi)
  Makanan       → 5-15%
  Rumah tangga  → 5-15%
  Hobi/Olahraga → 10-20%
"""

from __future__ import annotations

from typing import Any

from Services.agents.base import AgentContext, BaseAgent


class CommissionHunterAgent(BaseAgent):
    """Find products with the highest affiliate commission potential."""

    COMMISSION_RATES = {
        "elektronik": (0.01, 0.05),
        "fashion": (0.10, 0.20),
        "kesehatan": (0.10, 0.25),
        "kecantikan": (0.15, 0.30),
        "makanan": (0.05, 0.15),
        "rumah_tangga": (0.05, 0.15),
        "hobi": (0.10, 0.20),
        "otomotif": (0.03, 0.10),
        "ibu_anak": (0.10, 0.20),
        "umum": (0.05, 0.15),
    }

    # Produk dengan komisi tinggi berdasarkan kategori
    HIGH_COMMISSION_NICHES = {
        "kecantikan": ["skincare", "makeup", "serum wajah", "body care"],
        "kesehatan": ["vitamin", "suplemen", "alat kesehatan"],
        "fashion": ["hijab", "tas", "sepatu", "jam tangan"],
        "hobi": ["camera", "handmade", "craft"],
        "makanan": ["kopi", "snack sehat", "camilan"],
    }

    def __init__(self):
        pass

    async def execute(
        self,
        ctx: AgentContext,
        keyword: str = "",
        category: str = "umum",
        platform: str = "shopee",
        max_results: int = 10,
        min_commission_rp: float = 5000,
        use_reach: bool = False,
        **kwargs: Any,
    ) -> dict:
        """Find top products by commission potential.

        Args:
            keyword: Product keyword to search
            category: Product category (affects commission rate)
            platform: shopee / tokopedia / tiktokshop / all
            max_results: Number of top products to return
            min_commission_rp: Minimum commission in IDR
            use_reach: Use Agent-Reach for real social discovery

        Returns:
            Ranked products with commission estimates

        """
        # 1. Get commission rate range for this category
        rate_min, rate_max = self.COMMISSION_RATES.get(category, (0.05, 0.15))
        avg_rate = (rate_min + rate_max) / 2

        # 2. Discover products via ScrapeAgent
        from Services.agents.scraper import ScrapeAgent
        scraper = ScrapeAgent(use_reach=use_reach)

        # If no keyword, try trending products
        if not keyword:
            trending = await scraper.discover_trending(category=category)
            keywords = self.HIGH_COMMISSION_NICHES.get(category, ["produk terlaris"])
            keyword = trending.get("keyword", keywords[0]) if trending else keywords[0]

        products = await scraper.search_products(
            keyword=keyword,
            platform=platform,
            max_results=max_results * 2,
        )

        # 3. Calculate commission for each product
        scored = []
        for p in products:
            price = p.get("price", 0) or 0
            sales = p.get("sales", 0) or 0

            if price <= 0:
                continue

            # Commission calculation
            commission_per_item = price * avg_rate
            commission_min = price * rate_min
            commission_max = price * rate_max

            # Monthly earning potential
            monthly_potential = commission_per_item * max(sales // 30, 1)

            # Final score: weighted
            commission_score = min(commission_per_item / 50000 * 40, 40)  # higher commission = better
            sales_score = min(sales / 5000 * 30, 30)  # more sales = better
            niche_score = 20 if category in self.HIGH_COMMISSION_NICHES else 10  # niche bonus
            total_score = commission_score + sales_score + niche_score

            scored.append({
                **p,
                "commission_estimate": {
                    "rate_min_pct": round(rate_min * 100, 1),
                    "rate_max_pct": round(rate_max * 100, 1),
                    "avg_rate_pct": round(avg_rate * 100, 1),
                    "commission_per_item": round(commission_per_item),
                    "commission_range_rp": f"Rp{round(commission_min):,} - Rp{round(commission_max):,}",
                    "monthly_potential_rp": round(monthly_potential),
                },
                "profit_score": round(total_score, 1),
                "category": category,
            })

        # 4. Sort by profit score descending
        scored.sort(key=lambda x: x["profit_score"], reverse=True)

        # 5. Filter by minimum commission
        scored = [s for s in scored if s["commission_estimate"]["commission_per_item"] >= min_commission_rp]

        # 6. Return top results
        top = scored[:max_results]

        await ctx.session.commit()
        return {
            "query": {"keyword": keyword, "category": category, "platform": platform},
            "commission_rate": {"min": round(rate_min * 100, 1), "max": round(rate_max * 100, 1), "avg": round(avg_rate * 100, 1)},
            "total_found": len(products),
            "qualified": len(top),
            "top_products": top,
            "recommendation": self._recommend(top[:3]) if top else "No products found",
        }

    def _recommend(self, top_products: list) -> str:
        """Generate human recommendation from top products."""
        if not top_products:
            return ""
        best = top_products[0]
        com = best.get("commission_estimate", {})
        return (
            f"🏆 Rekomendasi: **{best.get('title', '')}** — "
            f"Komisi Rp{com.get('commission_per_item', 0):,}/item, "
            f"potensi Rp{com.get('monthly_potential_rp', 0):,}/bulan. "
            f"Score: {best.get('profit_score', 0)}/100"
        )

    async def analyze_commission(self, price: float, category: str, sales: int = 0) -> dict:
        """Quick commission analysis for a known product price."""
        rate_min, rate_max = self.COMMISSION_RATES.get(category, (0.05, 0.15))
        avg_rate = (rate_min + rate_max) / 2
        com_per_item = price * avg_rate
        monthly = com_per_item * max(sales // 30, 1) if sales else 0

        return {
            "price": price,
            "category": category,
            "rate": f"{rate_min*100:.0f}-{rate_max*100:.0f}%",
            "commission_per_item": round(com_per_item),
            "commission_range_rp": f"Rp{round(price * rate_min):,} - Rp{round(price * rate_max):,}",
            "monthly_potential_rp": round(monthly) if sales else "N/A (need sales data)",
            "verdict": "💎 HIGH" if com_per_item >= 50000 else "👍 MEDIUM" if com_per_item >= 10000 else "👎 LOW",
        }
