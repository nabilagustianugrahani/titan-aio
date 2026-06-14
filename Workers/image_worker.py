"""Kaggle image worker — runs FLUX Schnell/Dev on real Kaggle T4."""

from __future__ import annotations

import json
import os
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any, Optional

import redis as sync_redis


class ImageWorker:
    """Image generation worker. Runs locally (simulated) or dispatches to Kaggle."""

    def __init__(self, worker_id: str = "image-worker-1", use_kaggle: bool = False) -> None:
        self.worker_id = worker_id
        self.use_kaggle = use_kaggle
        self._redis: Optional[sync_redis.Redis] = None

    @property
    def redis(self) -> sync_redis.Redis:
        if self._redis is None:
            from titan.config import settings
            self._redis = sync_redis.from_url(settings.REDIS_URL, decode_responses=True)
        return self._redis

    async def process_job(self, job: dict) -> dict:
        """Process an image generation job."""
        if self.use_kaggle:
            return self._dispatch_to_kaggle(job)
        return self._simulate(job)

    def _simulate(self, job: dict) -> dict:
        """Simulated generation for local dev."""
        prompt = job.get("payload", {}).get("prompt", "")
        model = job.get("payload", {}).get("model", "flux-schnell")
        time.sleep(0.1)
        return {
            "worker_id": self.worker_id,
            "job_id": job["job_id"],
            "status": "completed",
            "output": {
                "image_url": f"https://storage.titan-aio.local/images/{job['job_id']}.png",
                "model_used": model,
                "generation_time_ms": 1500,
            },
        }

    def _dispatch_to_kaggle(self, job: dict) -> dict:
        """Enqueue to Redis for Kaggle to pick up."""
        self.redis.rpush("queue:image", json.dumps(job))
        return {
            "worker_id": self.worker_id,
            "job_id": job["job_id"],
            "status": "dispatched",
            "note": "Sent to Kaggle image-worker queue",
        }

    async def health(self) -> dict:
        """Return worker health."""
        return {
            "worker_id": self.worker_id,
            "status": "ready",
            "gpu": "T4 (Kaggle)" if self.use_kaggle else "simulated",
            "models": ["flux-schnell", "flux-dev"],
            "mode": "kaggle" if self.use_kaggle else "simulated",
        }

    @staticmethod
    def generate_notebook_script() -> str:
        """Return the Kaggle notebook content for image worker."""
        path = Path(__file__).parent / "kaggle_image_notebook.py"
        if path.exists():
            return path.read_text()
        return "# Notebook not found"
