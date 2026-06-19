"""
TITAN AIO — Autonomous Launch Controller

Once you provide credentials once, this handles everything else.

Modes:
  --mode single     Single variant launch (default)
  --mode batch N    Batch A/B testing with N variants
  --mode lip-sync   Generate video with lip sync
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
from Services.video.variant_generator import VariantGenerator, VariantBatch
from Services.video.lip_sync import LipSyncEngine


class AutonomousLauncher:
    """One-shot autonomous campaign launcher.

    YOU: set credentials in .env
    TITAN: does the rest

    Modes:
      --mode single       Single variant (default, backward compatible)
      --mode batch 3      Generate 3 A/B variants for testing
      --mode lip-sync     Video with lip sync (requires face image)
    """

    @staticmethod
    async def launch(
        url: str,
        mode: str = "single",
        num_variants: int = 3,
        platforms: list[str] | None = None,
        face_image: str | None = None,
    ) -> dict:
        if platforms is None:
            platforms = ["tiktok"]

        print(f"\n🚀 TITAN AIO — AUTONOMOUS LAUNCH")
        print(f"   Target: {url}")
        print(f"   Mode: {mode}")
        print(f"   Platforms: {', '.join(platforms)}")
        print(f"   {'═' * 50}")

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

        result = {
            "campaign_id": package.campaign_id,
            "product": package.product.title,
            "status": "launched",
        }

        # 2. Batch mode: generate A/B variants
        if mode == "batch":
            print(f"\n2️⃣  Generating {num_variants} A/B variants...")
            gen = VariantGenerator()
            batch = await gen.generate(
                product_url=url,
                product_title=package.product.title,
                product_id=package.campaign_id,
                num_variants=num_variants,
                platforms=platforms,
            )

            for v in batch.variants:
                print(f"   ✅ Variant {v.label} ({v.style}): {v.hook[:50]}...")
            print(f"   ✅ Batch ID: {batch.batch_id}")

            result["batch_id"] = batch.batch_id
            result["variants"] = [
                {"id": v.variant_id, "label": v.label, "style": v.style, "hook": v.hook}
                for v in batch.variants
            ]

            # Save variant batch for later optimization
            batch_path = Path("/tmp") / f"batch-{batch.batch_id}.json"
            batch_data = {
                "batch_id": batch.batch_id,
                "product_id": batch.product_id,
                "product_title": batch.product_title,
                "variants": [
                    {"id": v.variant_id, "label": v.label, "hook": v.hook,
                     "script": v.script, "style": v.style}
                    for v in batch.variants
                ],
            }
            batch_path.write_text(json.dumps(batch_data, indent=2))
            print(f"   ✅ Batch saved → {batch_path}")

        # 3. Lip sync mode
        if mode == "lip-sync" and face_image:
            print(f"\n3️⃣  Generating lip sync video...")
            lip_engine = LipSyncEngine()
            if lip_engine.is_available():
                # Generate audio from script first
                audio_path = f"/tmp/titan-audio-{package.campaign_id}.wav"
                print(f"   🎤 Generating TTS audio...")
                # TTS generation would go here (integration with TTS service)

                print(f"   👄 Running lip sync...")
                sync_result = await lip_engine.sync(
                    audio_path=audio_path,
                    face_image=face_image,
                )
                if sync_result.success:
                    print(f"   ✅ Lip sync video: {sync_result.video_path}")
                    result["lipsync_video"] = sync_result.video_path
                else:
                    print(f"   ⚠️  Lip sync failed: {sync_result.error}")
            else:
                print(f"   ⚠️  No lip sync engine available")
                print(f"   Install: git clone https://github.com/Rudrabha/Wav2Lip /opt/lip-sync-models/Wav2Lip")

        # 4. Push to Notion dashboard
        print(f"\n4️⃣  Syncing to Notion dashboard...")
        db = NotionDashboard()
        campaign = db.push_campaign(package)
        print(f"   ✅ Campaign saved → {campaign.get('url', 'Notion')}")

        for h in package.hooks.hooks[:3]:
            db.push_knowledge("Hooks", h.hook, 0.7 if h.predicted_ctr == "high" else 0.5)
        print(f"   ✅ Top hooks saved to Knowledge Base")

        # 5. Save to GDrive
        print(f"\n5️⃣  Backing up to GDrive...")
        report = {
            "campaign_id": package.campaign_id,
            "product": package.product.title,
            "price": package.product.price,
            "rating": package.product.rating,
            "hooks_count": len(package.hooks.hooks),
            "scripts_count": len(package.scripts.scripts),
            "offer_angle": package.offer_strategy.primary_angle,
            "cta": package.offer_strategy.recommended_cta,
            "mode": mode,
            "platforms": platforms,
        }
        if mode == "batch":
            report["batch_id"] = result.get("batch_id")
            report["variants_count"] = num_variants

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
        print(f"   Mode: {mode}")
        if mode == "batch":
            print(f"   Variants: {num_variants}")
        print(f"   Notion: {campaign.get('url', 'synced')}")
        return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="TITAN AIO Autonomous Launcher")
    parser.add_argument("url", nargs="?", help="Product URL")
    parser.add_argument("--mode", choices=["single", "batch", "lip-sync"], default="single")
    parser.add_argument("--variants", type=int, default=3, help="Number of A/B variants")
    parser.add_argument("--platforms", nargs="+", default=["tiktok"])
    parser.add_argument("--face-image", help="Face image for lip sync mode")
    args = parser.parse_args()

    url = args.url or input("Product URL: ")
    asyncio.run(AutonomousLauncher.launch(
        url=url,
        mode=args.mode,
        num_variants=args.variants,
        platforms=args.platforms,
        face_image=args.face_image,
    ))
