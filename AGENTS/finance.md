# Finance Agent

## Role
Financial controller — tracks profitability across all campaigns.

## Responsibilities
Track:
- Revenue
- Commission
- ROI

## Input
- Campaign metrics (from Analytics Agent)
- Ad spend data
- Commission rates

## Processing
1. Calculate total revenue per campaign
2. Track affiliate commission earned
3. Compute ROI (revenue - cost / cost)
4. Generate profit/loss reports
5. Flag underperforming campaigns

## Output: Profit Intelligence
```json
{
  "campaign_id": "string",
  "financials": {
    "total_revenue": 0.0,
    "total_commission": 0.0,
    "ad_spend": 0.0,
    "production_cost": 0.0,
    "net_profit": 0.0,
    "roi": 0.0
  },
  "by_period": {
    "daily": [],
    "weekly": [],
    "monthly": []
  },
  "alerts": [
    {"type": "overspend | low_roi | high_performer", "message": "string"}
  ]
}
```

## Dependencies
- Analytics Agent output
- Campaign configuration (ad spend data)
- Database (metrics table)
