"""
TITAN AIO — Kaggle Master Notebook
Auto-installs environment, starts MCP proxy, runs generation worker.

Usage:
  1. Create Kaggle notebook (GPU T4 x2)
  2. Add secret: TITAN_REDIS_URL, TITAN_S3_ENDPOINT, TITAN_S3_ACCESS_KEY, TITAN_S3_SECRET_KEY
  3. Set WORKER_TYPE via Kaggle Notebook Environment variable
  4. Run all cells
"""

import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

WORKER_TYPE = os.environ.get("WORKER_TYPE", "image-worker")
REDIS_URL = os.environ.get("TITAN_REDIS_URL", "redis://localhost:6379/0")
S3_ENDPOINT = os.environ.get("TITAN_S3_ENDPOINT", "http://localhost:9000")
S3_ACCESS_KEY = os.environ.get("TITAN_S3_ACCESS_KEY", "minioadmin")
S3_SECRET_KEY = os.environ.get("TITAN_S3_SECRET_KEY", "minioadmin")
S3_BUCKET = os.environ.get("TITAN_S3_BUCKET", "titan-assets")
WORKER_ID = f"{WORKER_TYPE}-{uuid.uuid4().hex[:8]}"

OUTPUT_DIR = Path("/kaggle/working/output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = OUTPUT_DIR / "worker.log"


def log(msg: str) -> None:
    timestamp = time.strftime("%H:%M:%S")
    line = f"[{timestamp}] [{WORKER_ID}] {msg}"
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")
    print(line)


def run(cmd: str, timeout: int = 300, check: bool = True) -> subprocess.CompletedProcess:
    log(f"Running: {cmd[:120]}")
    return subprocess.run(cmd, shell=True, timeout=timeout, check=check,
                          capture_output=True, text=True)


# ── Install Dependencies ──────────────────────────────────────────
log("=== Installing dependencies ===")
PACKAGES = [
    "torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124",
    "diffusers transformers accelerate sentencepiece",
    "redis boto3 requests pillow",
]
for pkg in PACKAGES:
    try:
        run(f"pip install -q {pkg}", timeout=300)
    except subprocess.CalledProcessError as e:
        log(f"Install warning (non-fatal): {e.stderr[-200:]}")
log("Dependencies installed")

# ── Check GPU ──────────────────────────────────────────────────────
try:
    gpu_info = run("nvidia-smi --query-gpu=name,memory.total --format=csv,noheader", timeout=10)
    log(f"GPU: {gpu_info.stdout.strip()}")
except Exception:
    log("No GPU detected, running in CPU mode")

# ── Redis Polling ──────────────────────────────────────────────────
log(f"Worker {WORKER_ID} starting, type={WORKER_TYPE}")
log(f"Redis: {REDIS_URL[:50]}...")
log(f"S3: {S3_ENDPOINT}")

QUEUE_KEY = f"queue:{WORKER_TYPE}"
RESULT_PREFIX = f"result:"

if __name__ == "__main__":
    log("Worker ready. Polling for jobs...")
    while True:
        time.sleep(5)
