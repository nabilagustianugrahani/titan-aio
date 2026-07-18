"""MCP singleton instance to avoid circular imports."""
from __future__ import annotations

from fastmcp import FastMCP

mcp = FastMCP("titan-aio")
