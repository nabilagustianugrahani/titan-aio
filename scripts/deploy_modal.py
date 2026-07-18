#!/usr/bin/env python3
"""TITAN AIO — Deploy Modal Workers from HF Spaces.

One-time deployment script. Runs from HF Space to deploy GPU workers to Modal.

Usage:
    python scripts/deploy_modal.py

Requires:
    - MODAL_TOKEN_ID and MODAL_TOKEN_SECRET in env
    - modal package installed
"""

import os
import subprocess
import sys
from pathlib import Path


def deploy():
    """Deploy Modal workers."""
    # Check Modal credentials
    token_id = os.environ.get("MODAL_TOKEN_ID", "")
    token_secret = os.environ.get("MODAL_TOKEN_SECRET", "")

    if not token_id or not token_secret:
        print("❌ MODAL_TOKEN_ID and MODAL_TOKEN_SECRET required")
        sys.exit(1)

    # Set Modal credentials
    os.environ["MODAL_TOKEN_ID"] = token_id
    os.environ["MODAL_TOKEN_SECRET"] = token_secret

    # Deploy workers
    workers_dir = Path(__file__).parent.parent / "Workers"

    print("🚀 Deploying Modal workers...")

    # Deploy FLUX (A100)
    print("\n1️⃣  Deploying FLUX (A100)...")
    result = subprocess.run(
        ["modal", "deploy", str(workers_dir / "modal_a100.py")],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print("✅ FLUX deployed!")
    else:
        print(f"❌ FLUX failed: {result.stderr[:200]}")

    # Deploy SD3.5 (T4)
    print("\n2️⃣  Deploying SD3.5 (T4)...")
    result = subprocess.run(
        ["modal", "deploy", str(workers_dir / "modal_image.py")],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print("✅ SD3.5 deployed!")
    else:
        print(f"❌ SD3.5 failed: {result.stderr[:200]}")

    print("\n✅ Deployment complete!")
    print("   Modal workers are now available via API.")


if __name__ == "__main__":
    deploy()
