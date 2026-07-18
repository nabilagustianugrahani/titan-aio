"""MCP tools module."""

from __future__ import annotations

from MCP.instance import mcp

_mgr = None

def _get_mgr():
    global _mgr
    if _mgr is None:
        from Services.content.versioning import ContentVersionManager
        _mgr = ContentVersionManager()
    return _mgr


@mcp.tool()
async def create_content_version(content_type: str, content_id: str, content: str, author: str = "system", notes: str = "") -> dict:
    """Create a new version of content. Auto-increments version number."""
    mgr = _get_mgr()
    result = await mgr.create_version(content_type=content_type, content_id=content_id, content=content, author=author, notes=notes)
    return result.model_dump()


@mcp.tool()
async def get_content_versions(content_type: str, content_id: str) -> list[dict]:
    """Get all versions of a content piece."""
    mgr = _get_mgr()
    versions = await mgr.get_versions(content_type=content_type, content_id=content_id)
    return [v.model_dump() for v in versions]


@mcp.tool()
async def revert_content_version(content_type: str, content_id: str, version_id: str) -> dict:
    """Revert content to a specific version."""
    mgr = _get_mgr()
    result = await mgr.revert(content_type=content_type, content_id=content_id, version_id=version_id)
    return result.model_dump() if result else {"error": "Version not found"}


@mcp.tool()
async def compare_content_versions(content_type: str, content_id: str, version_1: str, version_2: str) -> dict:
    """Compare two versions of content side by side."""
    mgr = _get_mgr()
    return await mgr.compare(content_type=content_type, content_id=content_id, v1_id=version_1, v2_id=version_2)


@mcp.tool()
async def update_version_score(content_type: str, content_id: str, version_id: str, score: float) -> dict:
    """Update performance score for a content version."""
    mgr = _get_mgr()
    success = await mgr.update_score(content_type=content_type, content_id=content_id, version_id=version_id, score=score)
    return {"success": success, "version_id": version_id, "score": score}
