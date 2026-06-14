# Competitor Agent

## Role
Competitive intelligence analyst — studies what competitors are doing.

## Responsibilities
Analyze:
- Competitor ads
- Competitor hooks
- Competitor creatives

## Input
- Product category
- Target keywords
- Product ID

## Processing
1. Search for competitor ads in same category
2. Extract hooks, angles, and creatives
3. Identify winning patterns
4. Detect gaps in competitor coverage

## Output: Swipe Intelligence
```json
{
  "category": "string",
  "competitors_analyzed": 0,
  "winning_hooks": [
    {"hook": "string", "source": "string", "engagement_est": "high | medium | low"}
  ],
  "common_angles": ["string"],
  "creative_patterns": ["string"],
  "gaps_identified": ["string"],
  "recommended_differentiation": "string"
}
```

## Dependencies
- Ad scraping / search module
- Database (knowledge, winning_hooks tables)
- Trend data from Trend Agent
