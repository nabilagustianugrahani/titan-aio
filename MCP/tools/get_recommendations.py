"""Get recommendations based on winning hooks/products."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from Database.connection import get_session
from Database.models import WinningHook
from Database.repository import Repository
from MCP.schemas import (
    GetRecommendationsInput,
    GetRecommendationsOutput,
    Recommendation,
)


async def get_recommendations(
    input_data: GetRecommendationsInput,
    session: Optional[AsyncSession] = None,
) -> GetRecommendationsOutput:
    """Get recommendations from historical campaign data."""
    own_session = False
    if session is None:
        own_session = True
        async for s in get_session():
            session = s
            break

    try:
        repo = Repository(session, WinningHook)
        all_hooks = await repo.list_all(limit=input_data.limit)

        recs = []
        for h in all_hooks:
            ctr_label = "medium"
            if h.ctr is not None:
                ctr_label = "high" if h.ctr > 0.05 else "medium"
            recs.append(
                Recommendation(
                    hook=h.hook_text,
                    category="general",
                    predicted_ctr=ctr_label,
                    source_campaign_id=h.campaign_id,
                )
            )

        return GetRecommendationsOutput(recommendations=recs, total=len(recs))
    finally:
        if own_session:
            await session.close()
