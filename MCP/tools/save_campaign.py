"""Save campaign to database."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from Database.connection import get_session
from Database.models import Campaign
from Database.repository import Repository
from MCP.schemas import SaveCampaignInput, SaveCampaignOutput


async def save_campaign(
    input_data: SaveCampaignInput,
    session: Optional[AsyncSession] = None,
) -> SaveCampaignOutput:
    """Save a campaign to the database."""
    own_session = False
    if session is None:
        own_session = True
        async for s in get_session():
            session = s
            break

    try:
        repo = Repository(session, Campaign)
        campaign = await repo.create(
            product_id=input_data.product_id,
            name=input_data.name,
            platform=input_data.platform,
            budget=input_data.budget,
            config=input_data.config,
        )
        return SaveCampaignOutput(campaign_id=campaign.id, status=campaign.status)
    finally:
        if own_session:
            await session.close()
