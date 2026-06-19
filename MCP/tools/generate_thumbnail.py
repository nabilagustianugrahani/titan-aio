"""Generate thumbnail concepts via ContentAgent."""

from __future__ import annotations

from MCP.schemas import GenerateThumbnailInput, GenerateThumbnailOutput
from Services.agents.content import ContentAgent


async def generate_thumbnail(input_data: GenerateThumbnailInput) -> GenerateThumbnailOutput:
    """Generate thumbnail concept using ContentAgent."""
    agent = ContentAgent()

    from Database.connection import async_session_factory
    async with async_session_factory() as session:
        from Services.agents.base import AgentContext
        ctx = AgentContext(session=session)
        result = await agent.execute(
            ctx,
            product_id=input_data.product_id,
            category="umum",
        )
        return result.get("thumbnail", GenerateThumbnailOutput(product_id=input_data.product_id))
