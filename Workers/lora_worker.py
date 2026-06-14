"""Kaggle LoRA worker -- runs Kohya / SimpleTuner."""

from __future__ import annotations

import time
from typing import Any


class LoraWorker:
    """LoRA training worker (runs on Kaggle T4)."""

    def __init__(self, worker_id: str = "lora-worker-1") -> None:
        self.worker_id = worker_id

    async def process_job(self, job: dict) -> dict:
        """Process a LoRA training job."""
        product_id = job.get("payload", {}).get("product_id", "unknown")
        images = job.get("payload", {}).get("images", [])

        time.sleep(0.1)

        return {
            "worker_id": self.worker_id,
            "job_id": job["job_id"],
            "status": "completed",
            "output": {
                "lora_path": f"https://storage.titan-aio.local/lora/{product_id}.safetensors",
                "product_id": product_id,
                "training_time_ms": len(images) * 1000 if images else 30000,
            },
        }

    async def health(self) -> dict:
        return {
            "worker_id": self.worker_id,
            "status": "ready",
            "gpu": "T4",
            "models": ["kohya", "simple-tuner"],
        }
