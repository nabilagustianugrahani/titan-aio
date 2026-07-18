"""HuggingFace Hub client — singleton service for all HF operations.

Wraps huggingface_hub.HfApi for programmatic access and subprocess calls
to the `hf` CLI for operations not exposed in the library.

Usage:
    from Services.hf_client import hf_client
    info = await hf_client.space_info("Badjals/TitanAIO")
    models = await hf_client.hub_list_models(search="flux")
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
from pathlib import Path
from typing import Any

from titan.config import settings


class HFClient:
    """Singleton HuggingFace Hub client with lazy-init HfApi."""

    def __init__(self) -> None:
        self._api: Any = None
        self._token: str = ""

    # ── Internal helpers ────────────────────────────────────────────

    def _get_token(self) -> str:
        """Get HF_TOKEN from config or env."""
        if not self._token:
            self._token = settings.HF_TOKEN or os.environ.get("HF_TOKEN", "")
        return self._token

    def get_api(self) -> Any:
        """Lazy-init and return the HfApi instance."""
        if self._api is None:
            from huggingface_hub import HfApi
            token = self._get_token()
            self._api = HfApi(token=token)
        return self._api

    async def _run_hf_cli(self, *args: str, timeout: int = 60) -> dict | list | str:
        """Run `hf` CLI command and return parsed output (json or text).

        The `hf` CLI supports --format json for structured output.
        """
        cmd = ["hf", "--format", "json", *args]
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env={**os.environ, "HF_TOKEN": self._get_token()},
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout,
            )
            if proc.returncode != 0:
                msg = stderr.decode().strip() or f"exit code {proc.returncode}"
                return {"error": msg}
            text = stdout.decode().strip()
            if not text:
                return {"status": "ok"}
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text
        except asyncio.TimeoutError:
            return {"error": f"Command timed out after {timeout}s"}
        except FileNotFoundError:
            return {"error": "hf CLI not found — run `curl -LsSf https://hf.co/cli/install.sh | bash`"}
        except Exception as exc:
            return {"error": str(exc)}

    # ── Spaces Management ───────────────────────────────────────────

    async def space_info(self, space_id: str) -> dict:
        """Get Space runtime, hardware, domain, and stage info."""
        return await self._run_hf_cli("spaces", "info", space_id)

    async def space_logs(self, space_id: str, build: bool = False, tail: int = 50) -> list[str]:
        """Fetch Space logs (runtime or build)."""
        cmd = ["spaces", "logs", space_id, "--tail", str(tail)]
        if build:
            cmd.insert(2, "--build")
        result = await self._run_hf_cli(*cmd)
        if isinstance(result, list):
            return result
        if isinstance(result, dict) and "error" not in result:
            return [str(result)]
        return [f"error: {result.get('error', 'unknown')}"] if isinstance(result, dict) else [str(result)]

    async def space_restart(self, space_id: str) -> dict:
        """Restart a Space."""
        return await self._run_hf_cli("spaces", "restart", space_id)

    async def space_pause(self, space_id: str) -> dict:
        """Pause a Space."""
        return await self._run_hf_cli("spaces", "pause", space_id)

    async def space_set_hardware(self, space_id: str, hardware: str) -> dict:
        """Change Space hardware tier.

        Valid options: cpu-basic, cpu-upgrade, t4-small, t4-medium,
        l4x1, l4x4, a10g-small, a10g-large, a100-large, etc.
        """
        return await self._run_hf_cli("spaces", "settings", space_id, "--hardware", hardware)

    async def space_set_secret(self, space_id: str, key: str, value: str) -> dict:
        """Add or update a Space secret."""
        return await self._run_hf_cli(
            "spaces", "secrets", "add", space_id,
            "--secrets", f"{key}={value}",
        )

    async def space_list_secrets(self, space_id: str) -> list[str]:
        """List secret names for a Space (values are write-only, not returned)."""
        result = await self._run_hf_cli("spaces", "secrets", "list", space_id)
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            return list(result.keys()) if "error" not in result else [f"error: {result['error']}"]
        return [str(result)]

    async def space_delete_secret(self, space_id: str, key: str) -> dict:
        """Delete a Space secret."""
        return await self._run_hf_cli("spaces", "secrets", "delete", space_id, key, "--yes")

    async def space_set_env(self, space_id: str, key: str, value: str) -> dict:
        """Add or update a Space environment variable."""
        return await self._run_hf_cli(
            "spaces", "variables", "add", space_id,
            "--env", f"{key}={value}",
        )

    async def space_list_env(self, space_id: str) -> list[dict]:
        """List environment variables for a Space."""
        result = await self._run_hf_cli("spaces", "variables", "list", space_id)
        if isinstance(result, list):
            return result
        if isinstance(result, dict) and "error" not in result:
            return [result]
        return [{"error": result.get("error", "unknown")}] if isinstance(result, dict) else []

    async def space_toggle_dev_mode(self, space_id: str, stop: bool = False) -> dict:
        """Enable or disable Space dev mode."""
        cmd = ["spaces", "dev-mode", space_id]
        if stop:
            cmd.append("--stop")
        return await self._run_hf_cli(*cmd)

    async def space_wait(self, space_id: str, timeout: int = 300) -> dict:
        """Wait for a Space to finish building/starting."""
        return await self._run_hf_cli("spaces", "wait", space_id, "--timeout", str(timeout))

    # ── Hub Search / Browse ────────────────────────────────────────

    async def hub_list_models(
        self, search: str = "", author: str = "", sort: str = "downloads", limit: int = 10,
    ) -> list[dict]:
        """Search models on the Hub."""
        cmd = ["models", "list", "--limit", str(limit), "--sort", sort]
        if search:
            cmd.extend(["--search", search])
        if author:
            cmd.extend(["--author", author])
        result = await self._run_hf_cli(*cmd)
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            return [result]
        return []

    async def hub_list_datasets(
        self, search: str = "", author: str = "", limit: int = 10,
    ) -> list[dict]:
        """Search datasets on the Hub."""
        cmd = ["datasets", "list", "--limit", str(limit)]
        if search:
            cmd.extend(["--search", search])
        if author:
            cmd.extend(["--author", author])
        result = await self._run_hf_cli(*cmd)
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            return [result]
        return []

    async def hub_list_spaces(
        self, search: str = "", author: str = "", limit: int = 10,
    ) -> list[dict]:
        """Search Spaces on the Hub."""
        cmd = ["spaces", "list", "--limit", str(limit)]
        if search:
            cmd.extend(["--search", search])
        if author:
            cmd.extend(["--author", author])
        result = await self._run_hf_cli(*cmd)
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            return [result]
        return []

    async def hub_upload_file(
        self, repo_id: str, path: str, local_path: str, repo_type: str = "model",
    ) -> dict:
        """Upload a file to a Hub repository."""
        return await self._run_hf_cli(
            "upload", repo_id, local_path,
            "--path-in-repo", path,
            "--type", repo_type,
            "--commit-message", f"Upload {path} via Titan AIO",
        )

    async def hub_download_file(
        self, repo_id: str, path: str, repo_type: str = "model", local_dir: str = "",
    ) -> dict:
        """Download a file from a Hub repository."""
        cmd = ["download", repo_id, "--type", repo_type, "--include", path]
        if local_dir:
            cmd.extend(["--local-dir", local_dir])
        result = await self._run_hf_cli(*cmd)
        if isinstance(result, dict) and "error" not in result:
            result["local_path"] = str(Path(local_dir) / path) if local_dir else path
        return result

    # ── HF Jobs ─────────────────────────────────────────────────────

    async def job_list(self, status: str = "", limit: int = 20) -> list[dict]:
        """List HF Jobs, optionally filtered by status."""
        cmd = ["jobs", "list", "--limit", str(limit)]
        if status:
            cmd.extend(["--status", status.upper()])
        result = await self._run_hf_cli(*cmd)
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            return [result]
        return []

    async def job_run(
        self, image: str, command: str, flavor: str = "cpu-basic", timeout: int = 3600,
    ) -> dict:
        """Run a HF Job (containerized workload on HF infra)."""
        return await self._run_hf_cli(
            "jobs", "run", image, command,
            "--flavor", flavor,
            "--timeout", str(timeout),
            "--detach",
        )

    async def job_logs(self, job_id: str, tail: int = 50) -> list[str]:
        """Fetch logs for a HF Job."""
        result = await self._run_hf_cli("jobs", "logs", job_id, "--tail", str(tail))
        if isinstance(result, list):
            return result
        return [str(result)]

    async def job_cancel(self, job_id: str) -> dict:
        """Cancel a running HF Job."""
        return await self._run_hf_cli("jobs", "cancel", job_id)

    async def job_list_hardware(self) -> list[dict]:
        """List available hardware options for HF Jobs."""
        result = await self._run_hf_cli("jobs", "hardware")
        if isinstance(result, list):
            return result
        return [result] if isinstance(result, dict) else []

    # ── Collections ─────────────────────────────────────────────────

    async def collection_list(self, owner: str = "", limit: int = 20) -> list[dict]:
        """List HF Collections."""
        cmd = ["collections", "list", "--limit", str(limit)]
        if owner:
            cmd.extend(["--owner", owner])
        result = await self._run_hf_cli(*cmd)
        if isinstance(result, list):
            return result
        return [result] if isinstance(result, dict) else []

    async def collection_create(
        self, title: str, namespace: str = "", description: str = "", private: bool = False,
    ) -> dict:
        """Create a new HF Collection."""
        cmd = ["collections", "create", title]
        if namespace:
            cmd.extend(["--namespace", namespace])
        if description:
            cmd.extend(["--description", description])
        if private:
            cmd.append("--private")
        return await self._run_hf_cli(*cmd)

    async def collection_add_item(
        self, collection_slug: str, item_id: str, item_type: str = "model",
    ) -> dict:
        """Add an item to a HF Collection."""
        return await self._run_hf_cli(
            "collections", "add-item", collection_slug, item_id, item_type,
        )


# Module-level singleton
hf_client = HFClient()
