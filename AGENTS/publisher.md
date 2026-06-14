# Publisher Agent

## Role
Platform operator — formats and schedules content for distribution.

## Responsibilities
Prepare:
- Platform formatting
- Captions
- Hashtags
- Scheduling

## Supported Platforms
- TikTok
- Instagram Reels
- YouTube Shorts
- Facebook
- Shopee Feed
- Tokopedia Feed

## Input
- UGC Package (scripts, hooks, CTAs)
- Video Assets
- Image Assets

## Processing
1. Format content per platform specifications
2. Optimize caption length and structure per platform
3. Generate platform-specific hashtag sets
4. Determine optimal posting time (from Memory Agent)
5. Schedule posts

## Output: Publishing Package
```json
{
  "campaign_id": "string",
  "platforms": [
    {
      "platform": "tiktok | instagram | youtube | facebook | shopee | tokopedia",
      "content": {
        "caption": "string",
        "hashtags": ["string"],
        "cta": "string",
        "first_comment": "string"
      },
      "media": ["string"],
      "scheduled_time": "timestamp"
    }
  ]
}
```

## Dependencies
- Memory Agent (winning posting times)
- UGC Package
- Video Assets
- Campaign configuration
