"""Generate attention-grabbing hooks via ContentAgent."""

from __future__ import annotations

from MCP.schemas import GenerateHooksInput, GenerateHooksOutput
from Services.agents.content import ContentAgent


async def generate_hooks(input_data: GenerateHooksInput) -> GenerateHooksOutput:
    """Generate attention-grabbing hooks using ContentAgent."""
    agent = ContentAgent()

    # Use a minimal DB session for standalone MCP calls
    from Database.connection import async_session_factory
    async with async_session_factory() as session:
        from Services.agents.base import AgentContext
        ctx = AgentContext(session=session)
        result = await agent.execute(
            ctx,
            product_id=input_data.product_id,
            category="umum",
        )
        return result.get("hooks", GenerateHooksOutput(product_id=input_data.product_id))
