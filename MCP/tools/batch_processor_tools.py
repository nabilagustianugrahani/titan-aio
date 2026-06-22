"""MCP tools for Batch Processor."""

from __future__ import annotations

from MCP.server import mcp

_processor = None

def _get_processor():
    global _processor
    if _processor is None:
        from Services.campaign.batch_processor import BatchProcessor
        _processor = BatchProcessor()
    return _processor


@mcp.tool()
async def create_batch_job(items: str, concurrency: int = 3, delay: float = 1.0) -> dict:
    """Create a batch processing job. Items should be JSON array of objects."""
    import json
    processor = _get_processor()
    item_list = json.loads(items) if isinstance(items, str) else items
    result = await processor.create_batch(items=item_list, concurrency=concurrency, delay=delay)
    return result.model_dump()


@mcp.tool()
async def run_batch_job(job_id: str) -> dict:
    """Run a batch processing job."""
    processor = _get_processor()
    result = await processor.run_batch(job_id=job_id)
    return result.model_dump()


@mcp.tool()
async def get_batch_status(job_id: str) -> dict:
    """Get batch job status and progress."""
    processor = _get_processor()
    result = await processor.get_status(job_id=job_id)
    return result.model_dump() if result else {"error": "Job not found"}


@mcp.tool()
async def pause_batch_job(job_id: str) -> dict:
    """Pause a running batch job."""
    processor = _get_processor()
    success = await processor.pause_batch(job_id=job_id)
    return {"success": success, "job_id": job_id, "status": "paused" if success else "not_found"}


@mcp.tool()
async def list_batch_jobs(status: str = "") -> list[dict]:
    """List all batch jobs with optional status filter."""
    processor = _get_processor()
    jobs = await processor.list_jobs(status=status)
    return [j.model_dump() for j in jobs]


@mcp.tool()
async def get_batch_stats() -> dict:
    """Get batch processing statistics."""
    processor = _get_processor()
    return await processor.get_stats()
