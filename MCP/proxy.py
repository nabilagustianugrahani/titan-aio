"""
TITAN AIO — MCP Stdio-to-HTTP Proxy

Thin proxy that runs on VPS and forwards MCP tool calls to HF Space.
Used by Claude Code to connect to the Titan MCP server running on HF Space.

Usage:
    claude mcp add titan-aio -- python MCP/proxy.py

Or with env:
    claude mcp add titan-aio --env-file .env -- python MCP/proxy.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx

# ── Config ────────────────────────────────────────────────────────
HF_SPACE_URL = os.environ.get(
    "TITAN_HF_URL",
    "https://badjals-kopilampung.hf.space",
)
MCP_ENDPOINT = f"{HF_SPACE_URL}/mcp"
RETRY_DELAY = 30  # seconds to wait if HF Space is sleeping


def _forward_to_hf(payload: dict) -> dict | None:
    """Forward a JSON-RPC request to HF Space MCP endpoint."""
    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(
                MCP_ENDPOINT,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code in (502, 503):
                # HF Space might be waking up — wait and retry once
                import time
                print(f"[proxy] Space sleeping, waiting {RETRY_DELAY}s...", file=sys.stderr)
                time.sleep(RETRY_DELAY)
                resp = client.post(
                    MCP_ENDPOINT,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                if resp.status_code == 200:
                    return resp.json()
            print(f"[proxy] HTTP {resp.status_code}: {resp.text[:200]}", file=sys.stderr)
    except Exception as e:
        print(f"[proxy] Error: {e}", file=sys.stderr)
    return None


def main():
    """Read JSON-RPC from stdin, forward to HF Space, write response to stdout."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue

        response = _forward_to_hf(request)
        if response:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
        else:
            # Return JSON-RPC error
            error_resp = {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32000,
                    "message": "HF Space unavailable",
                },
            }
            sys.stdout.write(json.dumps(error_resp) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
