# Growth Agent

## Role
Growth optimizer — scales winners and cuts losers automatically.

## Responsibilities
Scale winning campaigns.
Terminate losing campaigns.

## Input
- Profit Intelligence (from Finance Agent)
- Campaign Metrics (from Analytics Agent)
- Knowledge Base (from Knowledge Agent)

## Processing
1. Evaluate each campaign against success thresholds:
   - ROI > threshold → scale
   - ROI < threshold → kill
2. For winning campaigns:
   - Increase ad spend
   - Generate creative variations
   - Expand to new platforms
3. For losing campaigns:
   - Pause ad spend
   - Archive campaign data
   - Log failure patterns to Memory Agent
4. Generate growth recommendations

## Output: Growth Strategy
```json
{
  "actions": [
    {
      "campaign_id": "string",
      "action": "scale | kill | iterate | maintain",
      "rationale": "string",
      "budget_change": 0.0,
      "expected_impact": "string"
    }
  ],
  "growth_recommendations": [
    {
      "category": "string",
      "action": "string",
      "expected_roi": 0.0
    }
  ]
}
```

## Success Thresholds (Default)
- **Scale**: ROI > 2.0 (200%) or as configured
- **Kill**: ROI < 0.5 (50%) for 2+ consecutive periods
- **Iterate**: ROI between thresholds, test variations
- **Maintain**: ROI stable at acceptable level, optimize incrementally

## Dependencies
- Finance Agent
- Analytics Agent
- Knowledge Agent
- Campaign management system
