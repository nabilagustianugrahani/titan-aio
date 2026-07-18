"""MCP tools for HuggingFace Spaces management.

Self-registering pattern: imports mcp from MCP.instance and uses @mcp.tool().

All tools return dict or list[dict] for FastMCP serialization.
"""

from __future__ import annotations

from Services.hf_client import hf_client
from MCP.instance import mcp


@mcp.tool()
async def hf_space_info(space_id: str) -> dict:
    """Get detailed info about a HuggingFace Space.

    Returns runtime stage, hardware, domain status, replicas, and metadata.

    Args:
        space_id: Full Space ID e.g. "Badjals/TitanAIO" or "username/space-name".
    """
    result = await hf_client.space_info(space_id)
    return result if isinstance(result, dict) else {"data": result}


@mcp.tool()
async def hf_space_logs(space_id: str, build: bool = False, tail: int = 50) -> list[str]:
    """Fetch runtime or build logs from a HuggingFace Space.

    Args:
        space_id: Full Space ID e.g. "Badjals/TitanAIO".
        build: True to fetch build logs instead of runtime logs.
        tail: Number of recent lines to return (default 50, max 200).

    Returns a list of log lines.
    """
    return await hf_client.space_logs(space_id, build=build, tail=min(tail, 200))


@mcp.tool()
async def hf_space_restart(space_id: str) -> dict:
    """Restart a HuggingFace Space.

    The Space will be unavailable for ~30-60s while it restarts.

    Args:
        space_id: Full Space ID e.g. "Badjals/TitanAIO".
    """
    return await hf_client.space_restart(space_id)


@mcp.tool()
async def hf_space_pause(space_id: str) -> dict:
    """Pause a HuggingFace Space to save compute credits.

    Paused Spaces can be restarted later. Saves on idle costs.

    Args:
        space_id: Full Space ID e.g. "Badjals/TitanAIO".
    """
    return await hf_client.space_pause(space_id)


@mcp.tool()
async def hf_space_set_hardware(space_id: str, hardware: str) -> dict:
    """Change the hardware tier for a HuggingFace Space.

    Common options:
      - cpu-basic (free, 2 vCPU, 16GB RAM)
      - cpu-upgrade (paid, 4 vCPU, 32GB RAM)
      - t4-small (paid, NVIDIA T4 16GB VRAM)
      - t4-medium (paid, 2x T4)
      - l4x1 (paid, NVIDIA L4 24GB VRAM)
      - a10g-small (paid, 1x A10G)
      - a100-large (paid, 1x A100)

    Args:
        space_id: Full Space ID e.g. "Badjals/TitanAIO".
        hardware: Hardware tier name (e.g. "cpu-basic", "t4-small").
    """
    return await hf_client.space_set_hardware(space_id, hardware)


@mcp.tool()
async def hf_space_secrets_list(space_id: str) -> list[str]:
    """List all secret names for a HuggingFace Space.

    Secret values are write-only and cannot be retrieved after being set.

    Args:
        space_id: Full Space ID e.g. "Badjals/TitanAIO".
    """
    return await hf_client.space_list_secrets(space_id)


@mcp.tool()
async def hf_space_secret_set(space_id: str, key: str, value: str) -> dict:
    """Add or update a secret in a HuggingFace Space.

    Secrets are environment variables that are encrypted at rest.
    Use for API keys, tokens, and credentials.

    Args:
        space_id: Full Space ID e.g. "Badjals/TitanAIO".
        key: Secret name (uppercase with underscores convention).
        value: Secret value (sensitive — not shown in logs).
    """
    return await hf_client.space_set_secret(space_id, key, value)


@mcp.tool()
async def hf_space_secret_delete(space_id: str, key: str) -> dict:
    """Delete a secret from a HuggingFace Space.

    Args:
        space_id: Full Space ID e.g. "Badjals/TitanAIO".
        key: Secret name to delete.
    """
    return await hf_client.space_delete_secret(space_id, key)


@mcp.tool()
async def hf_space_env_list(space_id: str) -> list[dict]:
    """List environment variables for a HuggingFace Space.

    Unlike secrets, env vars can be read back (non-sensitive config).

    Args:
        space_id: Full Space ID e.g. "Badjals/TitanAIO".
    """
    return await hf_client.space_list_env(space_id)


@mcp.tool()
async def hf_space_env_set(space_id: str, key: str, value: str) -> dict:
    """Add or update an environment variable in a HuggingFace Space.

    Use for non-sensitive configuration values visible in Space settings.

    Args:
        space_id: Full Space ID e.g. "Badjals/TitanAIO".
        key: Variable name.
        value: Variable value.
    """
    return await hf_client.space_set_env(space_id, key, value)


@mcp.tool()
async def hf_space_dev_mode(space_id: str, stop: bool = False) -> dict:
    """Toggle development mode on a HuggingFace Space.

    Dev mode allows SSH access into the running Space container for debugging.
    When enabled, the Space can be accessed via SSH.

    Args:
        space_id: Full Space ID e.g. "Badjals/TitanAIO".
        stop: Set to True to disable (stop) dev mode instead of enabling.
    """
    return await hf_client.space_toggle_dev_mode(space_id, stop=stop)


@mcp.tool()
async def hf_space_wait(space_id: str, timeout: int = 300) -> dict:
    """Wait for a HuggingFace Space to finish building or starting up.

    Polls the Space status until it's RUNNING or the timeout expires.

    Args:
        space_id: Full Space ID e.g. "Badjals/TitanAIO".
        timeout: Maximum wait time in seconds (default 300, max 600).
    """
    return await hf_client.space_wait(space_id, timeout=min(timeout, 600))
