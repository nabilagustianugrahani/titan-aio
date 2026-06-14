"""Load campaign from database."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from Database.connection import get_session
from Database.models import Campaign
from Database.repository import Repository
from MCP.schemas import LoadCampaignInput, LoadCampaignOutput


async def load_campaign(
    input_data: LoadCampaignInput,
    session: Optional[AsyncSession] = None,
) -> LoadCampaignOutput:
    """Load a campaign from the database."""
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
        return LoadCampaignOutput(
            campaign_id=campaign.id,
            product_id=campaign.product_id,
            name=campaign.name,
            status=campaign.status,
            platform=campaign.platform,
            budget=campaign.budget,
            total_spent=campaign.total_spent,
            total_revenue=campaign.total_revenue,
            created_at=campaign.created_at,
        )
    finally:
        if own_session:
            await session.close()
