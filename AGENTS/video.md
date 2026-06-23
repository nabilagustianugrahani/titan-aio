# Video Agent

## Role
Video producer — generates short-form ad creatives from scripts.

## Responsibilities
Generate:
- Short-form videos
- Ad creatives
- UGC videos

## Input
- UGC Package (scripts)
- Creative Package (storyboards, shot lists)
- Avatar Assets (if using avatar)
- Product images

## Processing
1. Parse script into scene segments
2. Match each scene with visual direction
3. Dispatch generation to video worker
4. Assemble segments into final video
5. Add captions/text overlays

## Output: Video Assets
```json
{
  "video_id": "string",
  "url": "string",
  "duration_seconds": 0,
  "format": "9:16 | 16:9 | 1:1",
  "script_title": "string",
  "model_used": "wan2.7-i2v | hunyuan_video",
  "processing_time_seconds": 0
}
```

## Generation Models
- **Wan 2.7 I2V (DashScope)**: Cloud API, no GPU needed, high quality
- **Wan 2.2 T2V (Modal GPU)**: Fallback, runs on A100 GPU
- **Hunyuan Video**: Higher quality, slower generation

## Dependencies
- GPU video worker
- S3 storage
- UGC Package
- Creative Package
