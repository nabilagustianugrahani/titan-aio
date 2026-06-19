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
3. Dispatch generation to Kaggle video-worker
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
  "model_used": "wan_2_2 | hunyuan_video",
  "processing_time_seconds": 0
}
```

## Generation Models
- **Wan 2.2**: General short-form, good motion consistency
- **Hunyuan Video**: Higher quality, slower generation

## Dependencies
- Kaggle video-worker
- S3 storage
- UGC Package
- Creative Package
