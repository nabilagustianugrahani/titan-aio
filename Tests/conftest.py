"""Test configuration — use SQLite to avoid needing PostgreSQL."""

from __future__ import annotations

import os
from pathlib import Path

# Set database to SQLite with absolute path
_TEST_DB = str(Path(__file__).resolve().parent.parent / "test.db")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:////{_TEST_DB.removeprefix('/')}"

# Import models so metadata registers all tables
import importlib, sys

# Ensure fresh reload
for mod in list(sys.modules.keys()):
    if "Database" in mod or "titan" in mod:
        del sys.modules[mod]

# Import ALL models so metadata registers every table before init_db
from Database.models import Product, Review, Campaign, AffiliateLink, GeneratedAsset
from Database.models import WinningHook, WinningProduct, WinningCTA, FailedCampaign
from Database.models import Metric, KnowledgeEntry, AvatarProfile, ProductProfile

# Now initialize the database (creates all registered tables)
from Database.connection import init_db, async_session_factory
import asyncio

asyncio.run(init_db())


# ── Seed test data ──────────────────────────────────────────────
async def _seed():
    from Database.models import Product, Metric, WinningHook
    from Database.repository import Repository
    from sqlalchemy import delete

    async with async_session_factory() as session:
        # Clear stale data first
        for model in [WinningHook, Metric, Product]:
            await session.execute(delete(model))
        await session.commit()

        repo_p = Repository(session, Product)
        repo_m = Repository(session, Metric)
        repo_h = Repository(session, WinningHook)

        # Seed products
        products = []
        for i, (title, cat, price, rating, sales) in enumerate([
            ("Power Bank 20000mAh Original", "elektronik", 89000, 4.5, 1200),
            ("Headset Bluetooth Wireless", "elektronik", 125000, 4.2, 800),
            ("Skincare Serum Vitamin C", "kecantikan", 65000, 4.7, 2500),
            ("Hijab Pashmina Premium", "fashion", 45000, 4.3, 1800),
            ("Snack Sehat Granola", "makanan", 35000, 4.1, 600),
        ]):
            p = await repo_p.create(
                external_id=f"test-prod-{i}",
                title=title,
                price=price,
                category=cat,
                rating=rating,
                total_sales=sales,
                url=f"https://shopee.co.id/product/{i}",
            )
            products.append(p)

        # Seed metrics
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        for p in products[:2]:
            await repo_m.create(
                campaign_id=p.id,
                platform="tiktok",
                views=5000,
                clicks=250,
                ctr=0.05,
                conversions=12,
                conversion_rate=0.048,
                revenue=150000.0,
                period_start=now - timedelta(days=7),
                period_end=now,
            )

        # Seed winning hooks
        for i, (text, htype, ctr) in enumerate([
            ("Harga termurah se-Indonesia!", "price_anchor", 0.065),
            ("Garansi resmi 1 tahun!", "trust_signal", 0.042),
            ("Cek review jujur di sini!", "social_proof", 0.038),
        ]):
            await repo_h.create(
                campaign_id=products[0].id,
                hook_text=text,
                hook_type=htype,
                ctr=ctr,
            )

        await session.commit()


asyncio.run(_seed())

