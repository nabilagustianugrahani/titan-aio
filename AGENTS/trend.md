# Trend Agent

## Role
Market intelligence scout — identifies what's hot and what's fading.

## Responsibilities
- Detect trends
- Detect viral products
- Detect market opportunities

## Analysis Sources
- Shopee trending page
- Tokopedia trending products
- Social media buzz detection
- Category velocity tracking

## Output: Trend Score
```json
{
  "product_id": "string",
  "trend_score": 0.0,
  "trend_direction": "up | down | stable",
  "velocity": "viral | fast | moderate | slow",
  "category": "string",
  "detected_at": "timestamp"
}
```

## When to Invoke
- Before product analysis (to prioritize high-trend items)
- Periodically for market scanning
- On user request

## Dependencies
- Database (products, metrics tables)
- Web scraping utilities
