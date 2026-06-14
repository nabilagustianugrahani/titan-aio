# TITAN AIO — Worker Specifications

## Architecture

```
User Flow → MCP Tools → GenerationRouter → Redis Queue → Kaggle Worker → S3
                                                              │
                                               ┌──────────────┼──────────────┐
                                               ▼              ▼              ▼
                                        image-worker   video-worker    lora-worker
                                        (FLUX T4)      (Wan 2.2 T4)   (Kohya T4)
```

## Workers

### 1. Image Worker (`image-worker`)
- **Model**: FLUX.1-schnell (default) / FLUX.1-dev
- **GPU**: T4 (Kaggle)
- **Input**: `{prompt, model, width, height}`
- **Output**: `{image_url, model_used, generation_time_ms}`
- **Queue**: `queue:image`
- **Notebook**: `Workers/kaggle_image_notebook.py`

### 2. Video Worker (`video-worker`)
- **Model**: Wan2.2-T2V-14B (default) / HunyuanVideo
- **GPU**: T4 (Kaggle)
- **Input**: `{script, model, duration}`
- **Output**: `{video_url, model_used, duration, generation_time_ms}`
- **Queue**: `queue:video`
- **Notebook**: `Workers/kaggle_video_notebook.py`

### 3. LoRA Worker (`lora-worker`)
- **Framework**: Kohya / SimpleTuner
- **GPU**: T4 (Kaggle)
- **Input**: `{product_id, images[]}`
- **Output**: `{lora_path, product_id, training_time_ms}`
- **Policy**: Train only if `product_usage_count > 20`
- **Queue**: `queue:lora`
- **Notebook**: `Workers/kaggle_lora_notebook.py`

## Rules
1. **Kaggle is generation infrastructure only** — no business logic, no orchestration.
2. Workers are **stateless** — all state in Redis/S3/DB.
3. Communication is **Redis-based** — `queue:*` for dispatch, `result:*` for response.
4. Results auto-expire from Redis after 1 hour.
5. Each worker has fallback to **simulated mode** when Kaggle is unavailable.
