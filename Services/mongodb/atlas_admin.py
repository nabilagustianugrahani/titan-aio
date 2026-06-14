"""MongoDB Atlas Admin API v2 client — manage clusters, IP access, backups."""

from __future__ import annotations

import base64
from typing import Any, Optional

import httpx

from titan.config import settings


class AtlasAdminClient:
    """MongoDB Atlas Admin API v2 client.

    Uses Digest HTTP auth with public+private API key.
    For read-only operations, only public key is needed.
    """

    BASE_URL = "https://cloud.mongodb.com/api/atlas/v2"

    def __init__(
        self,
        public_key: str = "",
        private_key: str = "",
        project_id: str = "",
    ) -> None:
        self.public_key = public_key or settings.MONGODB_PUBLIC_KEY
        self.private_key = private_key or settings.MONGODB_PRIVATE_KEY
        self.project_id = project_id or settings.MONGODB_PROJECT_ID

    @property
    def _auth(self) -> httpx.BasicAuth:
        return httpx.BasicAuth(self.public_key, self.private_key)

    async def _get(self, path: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/{path}",
                auth=self._auth,
                headers={"Accept": "application/vnd.atlas.2023-01-01+json"},
            )
            resp.raise_for_status()
            return resp.json()

    async def _patch(self, path: str, data: dict) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.patch(
                f"{self.BASE_URL}/{path}",
                auth=self._auth,
                headers={
                    "Accept": "application/vnd.atlas.2023-01-01+json",
                    "Content-Type": "application/json",
                },
                json=data,
            )
            resp.raise_for_status()
            return resp.json()

    async def _post(self, path: str, data: dict) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}/{path}",
                auth=self._auth,
                headers={
                    "Accept": "application/vnd.atlas.2023-01-01+json",
                    "Content-Type": "application/json",
                },
                json=data,
            )
            resp.raise_for_status()
            return resp.json()

    # ── Projects / Groups ──────────────────────────────────────

    async def list_projects(self) -> list[dict]:
        """List all Atlas projects."""
        data = await self._get("groups")
        return data.get("results", [])

    async def get_project(self, project_id: str = "") -> dict:
        pid = project_id or self.project_id
        return await self._get(f"groups/{pid}")

    # ── Clusters ───────────────────────────────────────────────

    async def list_clusters(self, project_id: str = "") -> list[dict]:
        pid = project_id or self.project_id
        data = await self._get(f"groups/{pid}/clusters")
        return data.get("results", [])

    async def get_cluster(self, cluster_name: str, project_id: str = "") -> dict:
        pid = project_id or self.project_id
        return await self._get(f"groups/{pid}/clusters/{cluster_name}")

    async def get_connection_string(self, cluster_name: str, project_id: str = "") -> str:
        """Get the SRV connection string for a cluster."""
        cluster = await self.get_cluster(cluster_name, project_id)
        conn = cluster.get("connectionStrings", {})
        return conn.get("standardSrv", "")

    # ── IP Access ──────────────────────────────────────────────

    async def list_ip_access(self, project_id: str = "") -> list[dict]:
        pid = project_id or self.project_id
        data = await self._get(f"groups/{pid}/accessList")
        return data.get("results", [])

    async def add_ip_access(self, ip: str, comment: str = "TITAN AIO Worker", project_id: str = "") -> dict:
        pid = project_id or self.project_id
        return await self._post(f"groups/{pid}/accessList", {
            "items": [{"ipAddress": ip, "comment": comment}],
        })

    # ── Database Users ─────────────────────────────────────────

    async def list_db_users(self, project_id: str = "") -> list[dict]:
        pid = project_id or self.project_id
        data = await self._get(f"groups/{pid}/databaseUsers")
        return data.get("results", [])

    # ── Checkpoints / Backups ──────────────────────────────────

    async def list_snapshots(self, cluster_name: str, project_id: str = "") -> list[dict]:
        pid = project_id or self.project_id
        data = await self._get(f"groups/{pid}/clusters/{cluster_name}/backup/snapshots")
        return data.get("results", [])
