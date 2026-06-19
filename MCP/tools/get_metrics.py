"""Get campaign metrics."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from Database.connection import get_session
from Database.models import Campaign
from Database.repository import Repository
from MCP.schemas import GetMetricsInput, GetMetricsOutput, PlatformMetrics


async def get_metrics(
    input_data: GetMetricsInput,
    session: Optional[AsyncSession] = None,
) -> GetMetricsOutput:
    """Get metrics for a campaign."""
    own_session = False
    if session is None:
        own_session = True
        async for s in get_session():
            session = s
            break

    try:
        repo = Repository(session, Campaign)
        campaign = await repo.get(input_data.campaign_id)

        if not campaign:
            raise ValueError(f"Campaign {input_data.campaign_id} not found")

        return GetMetricsOutput(
            campaign_id=input_data.campaign_id,
            metrics=PlatformMetrics(
                views=0,
                clicks=0,
                ctr=0.0,
                conversions=0,
                conversion_rate=0.0,
            ),
            total_revenue=campaign.total_revenue,
            total_commission=campaign.total_revenue * 0.05,
            roi=campaign.total_revenue / max(campaign.total_spent, 1) - 1,
        )
    finally:
        if own_session:
            await session.close()
