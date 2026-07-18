"""MCP tools for HuggingFace Hub search and file operations.

Self-registering pattern: imports mcp from MCP.instance and uses @mcp.tool().
"""

from __future__ import annotations

from Services.hf_client import hf_client
from MCP.instance import mcp


@mcp.tool()
async def hf_search_models(
    query: str = "",
    author: str = "",
    sort: str = "downloads",
    limit: int = 10,
) -> list[dict]:
    """Search for models on the HuggingFace Hub.

    Returns model ID, downloads, likes, pipeline tag, and last modified time.

    Args:
        query: Search keyword (e.g. "flux", "llama", "whisper").
        author: Filter by author/organization (e.g. "meta", "black-forest-labs").
        sort: Sort order — "downloads", "likes", "created_at", "last_modified", "trending_score".
        limit: Max results (default 10, max 100).
    """
    valid_sorts = {"downloads", "likes", "created_at", "last_modified", "trending_score"}
    if sort not in valid_sorts:
        sort = "downloads"
    return await hf_client.hub_list_models(
        search=query, author=author, sort=sort, limit=min(limit, 100),
    )


@mcp.tool()
async def hf_search_datasets(
    query: str = "",
    author: str = "",
    limit: int = 10,
) -> list[dict]:
    """Search for datasets on the HuggingFace Hub.

    Returns dataset ID, downloads, likes, and last modified time.

    Args:
        query: Search keyword (e.g. "imdb", "cifar", "squad").
        author: Filter by author/organization.
        limit: Max results (default 10, max 100).
    """
    return await hf_client.hub_list_datasets(
        search=query, author=author, limit=min(limit, 100),
    )


@mcp.tool()
async def hf_search_spaces(
    query: str = "",
    author: str = "",
    limit: int = 10,
) -> list[dict]:
    """Search for Spaces on the HuggingFace Hub.

    Returns Space ID, SDK, hardware, runtime stage, and likes.

    Args:
        query: Search keyword (e.g. "gradio", "llama", "text-to-image").
        author: Filter by author/organization.
        limit: Max results (default 10, max 100).
    """
    return await hf_client.hub_list_spaces(
        search=query, author=author, limit=min(limit, 100),
    )


@mcp.tool()
async def hf_upload_file(
    repo_id: str,
    path_in_repo: str,
    local_path: str,
    repo_type: str = "model",
) -> dict:
    """Upload a file to a HuggingFace Hub repository.

    Args:
        repo_id: Repository ID e.g. "username/my-model" or "org/dataset-name".
        path_in_repo: Destination path inside the repo (e.g. "config.json").
        local_path: Local file path to upload (absolute or relative to cwd).
        repo_type: Repository type — "model" (default), "dataset", or "space".
    """
    return await hf_client.hub_upload_file(
        repo_id=repo_id, path=path_in_repo,
        local_path=local_path, repo_type=repo_type,
    )


@mcp.tool()
async def hf_download_file(
    repo_id: str,
    path: str,
    repo_type: str = "model",
    local_dir: str = "",
) -> dict:
    """Download a file from a HuggingFace Hub repository.

    Args:
        repo_id: Repository ID e.g. "username/my-model".
        path: File path in the repo (e.g. "pytorch_model.bin").
        repo_type: Repository type — "model" (default), "dataset", or "space".
        local_dir: Local directory to save the file (default: current dir).
    """
    return await hf_client.hub_download_file(
        repo_id=repo_id, path=path, repo_type=repo_type, local_dir=local_dir,
    )
