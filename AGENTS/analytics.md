# Analytics Agent

## Role
Performance tracker — measures and reports campaign effectiveness.

## Responsibilities
Track:
- Views
- CTR
- Clicks
- Revenue
- Conversion Rate

## Input
- Campaign ID
- Platform metrics API data
- Conversion tracking data

## Processing
1. Collect metrics from platforms
2. Calculate derived metrics (CTR, conversion rate, ROI)
3. Compare against historical baselines
4. Generate performance report
5. Identify winning/losing variations

## Output: Campaign Metrics
```json
{
  "campaign_id": "string",
  "period": {
    "start": "timestamp",
    "end": "timestamp"
  },
  "metrics": {
    "views": 0,
    "clicks": 0,
    "ctr": 0.0,
    "conversions": 0,
    "conversion_rate": 0.0,
    "revenue": 0.0,
    "commission": 0.0,
    "roi": 0.0
  },
  "by_platform": {
    "platform_name": {
      "views": 0,
      "ctr": 0.0,
      "conversions": 0
    }
  },
  "top_performers": {
    "hooks": ["string"],
    "creatives": ["string"],
    "platforms": ["string"]
  }
}
```

## Dependencies
- Database (metrics table)
- Platform API connectors
- Finance Agent (for cost data)
