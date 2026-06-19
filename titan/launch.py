"""
TITAN AIO — Autonomous Launch Controller

Once you provide credentials once, this handles everything else.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:////" + str(Path(__file__).resolve().parent.parent / "data" / "titan.db"))

from MCP.tools.create_affiliate_package import create_affiliate_package
from MCP.schemas import CreateAffiliatePackageInput
from Services.notion.sync import NotionDashboard
from Services.gdrive.client import GoogleDriveClient


class AutonomousLauncher:
    """One-shot autonomous campaign launcher.

    YOU: set credentials in .env
    TITAN: does the rest
    """

    @staticmethod
    async def launch(url: str) -> dict:
        print(f"\n🚀 TITAN AIO — AUTONOMOUS LAUNCH")
        print(f"   Target: {url}")
        print(f"   { '═' * 50}")

        # 1. Generate full package
        print(f"\n1️⃣  Generating affiliate package...")
        package = await create_affiliate_package(
            CreateAffiliatePackageInput(url=url, include_video=True, include_avatar=True)
        )
        print(f"   ✅ Product: {package.product.title}")
        print(f"   ✅ {len(package.hooks.hooks)} hooks generated")
        print(f"   ✅ {len(package.scripts.scripts)} scripts generated")
        print(f"   ✅ Video: {'yes' if package.video else 'no'}")
        print(f"   ✅ Avatar: {'yes' if package.avatar else 'no'}")

        # 2. Push to Notion dashboard
        print(f"\n2️⃣  Syncing to Notion dashboard...")
        db = NotionDashboard()
        campaign = db.push_campaign(package)
        print(f"   ✅ Campaign saved → {campaign.get('url', 'Notion')}")

        for h in package.hooks.hooks[:3]:
            db.push_knowledge("Hooks", h.hook, 0.7 if h.predicted_ctr == "high" else 0.5)
        print(f"   ✅ Top hooks saved to Knowledge Base")

        # 3. Save to GDrive
        print(f"\n3️⃣  Backing up to GDrive...")
        report = {
            "campaign_id": package.campaign_id,
            "product": package.product.title,
            "price": package.product.price,
            "rating": package.product.rating,
            "hooks_count": len(package.hooks.hooks),
            "scripts_count": len(package.scripts.scripts),
            "offer_angle": package.offer_strategy.primary_angle,
            "cta": package.offer_strategy.recommended_cta,
        }
        report_path = Path("/tmp") / f"campaign-{package.campaign_id}.json"
        report_path.write_text(json.dumps(report, indent=2))
        try:
            gdrive = GoogleDriveClient.get_instance()
            gdrive.upload_file(str(report_path), mime_type="application/json")
            print(f"   ✅ Report uploaded to GDrive")
        except Exception as e:
            print(f"   ⚠️  GDrive upload skipped: {e}")

        print(f"\n{'═' * 50}")
        print(f"✅ LAUNCH COMPLETE")
        print(f"   Campaign ID: {package.campaign_id}")
        print(f"   Notion: {campaign.get('url', 'synced')}")
        return {"campaign_id": package.campaign_id, "status": "launched"}


if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else input("Product URL: ")
    asyncio.run(AutonomousLauncher.launch(url))
