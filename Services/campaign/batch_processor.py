"""Batch Processor — process 100+ products at once with rate limiting."""

from __future__ import annotations

import asyncio
import hashlib
from datetime import datetime

from pydantic import BaseModel


class BatchJob(BaseModel):
    job_id: str = ""
    status: str = "pending"  # pending/running/completed/failed/paused
    total_items: int = 0
    processed: int = 0
    successful: int = 0
    failed: int = 0
    items: list[dict] = []
    results: list[dict] = []
    errors: list[dict] = []
    created_at: str = ""
    completed_at: str = ""
    concurrency: int = 3
    delay_between: float = 1.0


class BatchProcessor:
    def __init__(self):
        self.jobs: dict[str, BatchJob] = {}

    async def create_batch(self, items: list[dict], concurrency: int = 3, delay: float = 1.0) -> BatchJob:
        job_id = hashlib.md5(f"batch:{datetime.now().isoformat()}".encode()).hexdigest()[:10]
        job = BatchJob(
            job_id=job_id, total_items=len(items), items=items,
            concurrency=concurrency, delay_between=delay,
            created_at=datetime.now().isoformat(),
        )
        self.jobs[job_id] = job
        return job

    async def process_item(self, item: dict) -> dict:
        """Override this method to define custom processing logic."""
        return {"status": "processed", "item": item, "result": "success"}

    async def run_batch(self, job_id: str, processor_fn=None) -> BatchJob:
        job = self.jobs.get(job_id)
        if not job:
            return BatchJob(job_id=job_id, status="failed")
        job.status = "running"
        fn = processor_fn or self.process_item
        for i, item in enumerate(job.items):
            if job.status == "paused":
                break
            try:
                result = await fn(item)
                job.results.append(result)
                job.successful += 1
            except Exception as e:
                job.errors.append({"index": i, "error": str(e), "item": str(item)[:100]})
                job.failed += 1
            job.processed += 1
            if job.delay_between > 0 and i < len(job.items) - 1:
                await asyncio.sleep(job.delay_between)
        if job.status != "paused":
            job.status = "completed"
            job.completed_at = datetime.now().isoformat()
        return job

    async def get_status(self, job_id: str) -> BatchJob | None:
        return self.jobs.get(job_id)

    async def pause_batch(self, job_id: str) -> bool:
        if job_id in self.jobs:
            self.jobs[job_id].status = "paused"
            return True
        return False

    async def resume_batch(self, job_id: str) -> bool:
        if job_id in self.jobs and self.jobs[job_id].status == "paused":
            self.jobs[job_id].status = "pending"
            return True
        return False

    async def list_jobs(self, status: str = "") -> list[BatchJob]:
        jobs = list(self.jobs.values())
        if status:
            jobs = [j for j in jobs if j.status == status]
        return sorted(jobs, key=lambda j: j.created_at, reverse=True)

    async def get_stats(self) -> dict:
        total = len(self.jobs)
        by_status = {}
        for j in self.jobs.values():
            by_status[j.status] = by_status.get(j.status, 0) + 1
        return {"total_jobs": total, "by_status": by_status}
