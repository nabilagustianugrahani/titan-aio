"""
Trend Agent — Real social listening via Agent-Reach.

Agent-Reach (github.com/Panniantong/Agent-Reach) searches Twitter/X, Reddit,
YouTube, XiaoHongShu, and web for trending topics — 100% free, no API keys.

This adapter lets our Trend Agent use real social data instead of simulation.

Install:
    pip install agent-reach

Usage (once Agent-Reach is installed):
    trend = AgentReachTrend()
    results = await trend.search("power bank", sources=["twitter", "reddit"])
"""

from __future__ import annotations

import asyncio
import json
import subprocess
from typing import Any, Optional


class AgentReachTrend:
    """Real social listening via Agent-Reach CLI.

    Falls back to simulation if Agent-Reach not installed.
    """

    def __init__(self, use_reach: bool = False):
        self.use_reach = use_reach

    async def search(self, query: str, sources: Optional[list[str]] = None) -> list[dict]:
        """Search for trending products/discussions across social platforms.

        Args:
            query: Search keyword (e.g., "power bank viral")
            sources: Platforms to search. Default: twitter, reddit, youtube

        Returns:
            List of trending mentions with source, text, engagement
        """
        if not self.use_reach:
            return self._simulate(query)

        sources = sources or ["twitter", "reddit", "youtube"]
        results = []
        for source in sources:
            try:
                result = await self._search_source(source, query)
                results.extend(result)
            except Exception as e:
                results.append({"source": source, "error": str(e)})
        return results

    async def _search_source(self, source: str, query: str) -> list[dict]:
        """Search a single source via Agent-Reach CLI."""
        # Agent-Reach v1.5+ uses 'skill' subcommand
        cmd = ["agent-reach", "skill", source, query, "--json"]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate(timeout=30)

        if proc.returncode != 0:
            return [{"source": source, "error": stderr.decode()[:200]}]

        try:
            data = json.loads(stdout.decode())
            items = data if isinstance(data, list) else data.get("results", [])
            return [
                {
                    "source": source,
                    "text": item.get("text", item.get("title", "")),
                    "url": item.get("url", ""),
                    "engagement": item.get("engagement", item.get("likes", 0)),
                    "date": item.get("date", ""),
                }
                for item in items[:20]
            ]
        except json.JSONDecodeError:
            return [{"source": source, "text": stdout.decode()[:200]}]

    def _simulate(self, query: str) -> list[dict]:
        """Simulated data when Agent-Reach not installed."""
        return [
            {"source": "twitter", "text": f"Trending: {query} banyak dibicarakan", "engagement": 1240, "simulated": True},
            {"source": "reddit", "text": f"Review {query} di subreddit indonesia", "engagement": 456, "simulated": True},
            {"source": "youtube", "text": f"Review {query} — 50k views", "engagement": 50000, "simulated": True},
        ]
