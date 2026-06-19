"""Asset Agent — collects and prepares product assets for campaigns."""
from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any, Optional

import httpx

from Services.agents.base import BaseAgent, AgentContext


class AssetAgent(BaseAgent):
    """Collects product images, review screenshots, logos for campaign creatives."""

    ASSET_DIR = Path("/tmp/titan-assets")

    async def execute(self, ctx: AgentContext, product_id: str = "", image_urls: list[str] | None = None, **kwargs: Any) -> dict:
        self.ASSET_DIR.mkdir(parents=True, exist_ok=True)
        campaign_dir = self.ASSET_DIR / product_id
        campaign_dir.mkdir(exist_ok=True)

        assets = {"product_images": [], "review_screenshots": [], "logo": "", "hero_image": ""}

        # Download product images
        if image_urls:
            for i, url in enumerate(image_urls[:5]):
                try:
                    ext = url.split(".")[-1][:4] if "." in url else "jpg"
                    path = campaign_dir / f"product_{i:02d}.{ext}"
                    async with httpx.AsyncClient(timeout=30) as client:
                        resp = await client.get(url)
                        if resp.status_code == 200:
                            path.write_bytes(resp.content)
                            assets["product_images"].append(str(path))
                except Exception:
                    pass

        # Create hero image placeholder
        hero = campaign_dir / "hero.jpg"
        if not hero.exists():
            from PIL import Image
            img = Image.new("RGB", (1024, 1024), color=(26, 26, 46))
            img.save(hero)
        assets["hero_image"] = str(hero)

        # Logo placeholder
        logo = campaign_dir / "logo.png"
        if not logo.exists():
            from PIL import Image
            img = Image.new("RGBA", (200, 200), color=(0, 0, 0, 0))
            img.save(logo)
        assets["logo"] = str(logo)

        await ctx.session.commit()
        return {
            "campaign_dir": str(campaign_dir),
            "assets": assets,
            "asset_count": len(assets["product_images"]),
        }
