"""Generation Router -- dispatches jobs to Kaggle workers via Redis."""

from __future__ import annotations

import json
import uuid
from typing import Any, Optional

import redis.asyncio as aioredis

from titan.config import settings


class GenerationRouter:
    """Routes generation jobs to appropriate Kaggle workers."""

    def __init__(self) -> None:
        self._redis: Optional[aioredis.Redis] = None
        self._queues = {
            "image": "queue:image",
            "video": "queue:video",
            "lora": "queue:lora",
        }

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        return self._redis

    async def dispatch(self, worker_type: str, payload: dict) -> dict:
        """Dispatch a job to the specified worker queue."""
        r = await self._get_redis()
        queue = self._queues.get(worker_type)
        if not queue:
            raise ValueError(f"Unknown worker type: {worker_type}")

        job = {
            "job_id": str(uuid.uuid4()),
            "type": worker_type,
            "payload": payload,
            "status": "queued",
        }
        await r.rpush(queue, json.dumps(job))
        return job

    async def poll_result(self, job_id: str, timeout: int = 300) -> Optional[dict]:
        """Poll for job result (simulated)."""
        r = await self._get_redis()
        result = await r.get(f"result:{job_id}")
        if result:
            return json.loads(result)
        return None

    async def close(self) -> None:
        if self._redis:
            await self._redis.close()
            self._redis = None
