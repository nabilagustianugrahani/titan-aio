"""Campaign Builder — packages everything into final campaign."""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

from Services.agents.base import AgentContext, BaseAgent


class CampaignBuilder(BaseAgent):
    """Assembles all campaign components into a deployable package."""

    async def execute(self, ctx: AgentContext, **kwargs: Any) -> dict:
        package = {
            "campaign_id": str(uuid.uuid4()),
            "created_at": datetime.utcnow().isoformat(),
            "product": kwargs.get("product", {}),
            "reviews": kwargs.get("reviews", {}),
            "competitors": kwargs.get("competitors", {}),
            "offer": kwargs.get("offer", {}),
            "hooks": kwargs.get("hooks", []),
            "scripts": kwargs.get("scripts", []),
            "assets": kwargs.get("assets", {}),
            "thumbnail": kwargs.get("thumbnail", ""),
            "images": kwargs.get("images", []),
            "video": kwargs.get("video", ""),
            "captions": kwargs.get("captions", {}),
            "affiliate_links": kwargs.get("affiliate_links", {}),
            "publishing": kwargs.get("publishing", {}),
        }

        await ctx.session.commit()
        return {
            "campaign_id": package["campaign_id"],
            "package_size_kb": len(json.dumps(package)) // 1024,
            "components": {k: bool(v) for k, v in package.items() if k not in ("campaign_id", "created_at")},
            "ready_to_deploy": True,
        }
