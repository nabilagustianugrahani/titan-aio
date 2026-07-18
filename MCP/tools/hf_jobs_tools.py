"""MCP tools for HuggingFace Jobs — run containerized GPU workloads on HF infra.

Self-registering pattern: imports mcp from MCP.instance and uses @mcp.tool().

HF Jobs are an alternative to Modal/Kaggle for running GPU workloads.
They support cpu-basic up to H200 GPUs.
"""

from __future__ import annotations

from Services.hf_client import hf_client
from MCP.instance import mcp


@mcp.tool()
async def hf_jobs_list(status: str = "", limit: int = 20) -> list[dict]:
    """List HuggingFace Jobs, with optional status filter.

    Args:
        status: Filter by status — "COMPLETED", "RUNNING", "ERROR", "CANCELED",
                "QUEUED", or "" for all.
        limit: Max results (default 20, max 100).
    """
    valid = {"", "COMPLETED", "RUNNING", "ERROR", "CANCELED", "QUEUED", "SCHEDULING"}
    if status.upper() not in valid:
        status = ""
    return await hf_client.job_list(status=status, limit=min(limit, 100))


@mcp.tool()
async def hf_jobs_run(
    image: str,
    command: str,
    flavor: str = "cpu-basic",
    timeout: int = 3600,
) -> dict:
    """Run a containerized Job on HuggingFace infrastructure.

    HF Jobs are an alternative to Modal or Kaggle for GPU workloads.
    The job runs a Docker image with the given command.

    Hardware flavors (flavor):
      - cpu-basic (free tier, 2 vCPU)
      - t4-small (NVIDIA T4 16GB)
      - t4-medium (2x T4)
      - l4x1 (NVIDIA L4 24GB)
      - a10g-small (NVIDIA A10G 24GB)
      - a100-large (NVIDIA A100 80GB)
      - h200 (NVIDIA H200 141GB)

    Args:
        image: Docker image to run (e.g. "python:3.11-slim").
        command: Command to execute inside the container.
        flavor: Hardware flavor (default "cpu-basic").
        timeout: Max runtime in seconds (default 3600 = 1h, max 86400).
    """
    return await hf_client.job_run(
        image=image, command=command, flavor=flavor, timeout=min(timeout, 86400),
    )


@mcp.tool()
async def hf_jobs_logs(job_id: str, tail: int = 50) -> list[str]:
    """Fetch logs for a HuggingFace Job.

    Args:
        job_id: The Job ID (e.g. "67f8a2b3c4d5e6f7a8b9c0d1").
        tail: Number of recent lines to return (default 50, max 200).
    """
    return await hf_client.job_logs(job_id, tail=min(tail, 200))


@mcp.tool()
async def hf_jobs_cancel(job_id: str) -> dict:
    """Cancel a running HuggingFace Job.

    Args:
        job_id: The Job ID to cancel.
    """
    return await hf_client.job_cancel(job_id)


@mcp.tool()
async def hf_jobs_hardware() -> list[dict]:
    """List all available hardware flavors for HuggingFace Jobs.

    Returns CPU/GPU type, vCPU count, memory, and hourly pricing.
    """
    return await hf_client.job_list_hardware()
