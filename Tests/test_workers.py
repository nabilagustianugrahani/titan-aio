"""Test Kaggle worker classes."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
class TestImageWorker:
    """Test image generation worker."""

    async def test_process_job(self):
        from Workers.image_worker import ImageWorker
        worker = ImageWorker()
        result = await worker.process_job(
            {
                "job_id": "test-1",
                "payload": {"prompt": "test image", "model": "flux-schnell"},
            }
        )
        assert result["status"] == "completed"
        assert result["output"]["image_url"]

    async def test_health(self):
        from Workers.image_worker import ImageWorker
        worker = ImageWorker()
        health = await worker.health()
        assert health["status"] == "ready"
        assert health["gpu"] in ("T4 (Kaggle)", "simulated")


@pytest.mark.asyncio
class TestVideoWorker:
    """Test video generation worker."""

    async def test_process_job(self):
        from Workers.video_worker import VideoWorker
        worker = VideoWorker()
        result = await worker.process_job(
            {
                "job_id": "test-1",
                "payload": {"script": "test script", "model": "wan-2-2"},
            }
        )
        assert result["status"] == "completed"


@pytest.mark.asyncio
class TestLoraWorker:
    """Test LoRA training worker."""

    async def test_process_job(self):
        from Workers.lora_worker import LoraWorker
        worker = LoraWorker()
        result = await worker.process_job(
            {
                "job_id": "test-1",
                "payload": {
                    "product_id": "p1",
                    "images": ["img1.png", "img2.png"],
                },
            }
        )
        assert result["status"] == "completed"
        assert result["output"]["lora_path"]
