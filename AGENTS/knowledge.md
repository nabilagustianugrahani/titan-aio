# Knowledge Agent

## Role
Knowledge synthesizer — converts raw campaign history into reusable intelligence.

## Responsibilities
Convert campaign history into reusable intelligence.

## Input
- Memory Agent data (all stored campaigns)
- Analytics Agent data (performance metrics)
- External research

## Processing
1. Analyze patterns across all campaigns
2. Identify transferable insights (e.g., "beauty products perform best with before/after hooks")
3. Generate category-specific playbooks
4. Update knowledge base with new patterns
5. Prune outdated or disproven knowledge

## Output: Knowledge Base
```json
{
  "knowledge_entries": [
    {
      "category": "string",
      "pattern": "string",
      "confidence": 0.0,
      "evidence": ["campaign_id"],
      "actionable_advice": "string"
    }
  ],
  "category_playbooks": [
    {
      "category": "string",
      "winning_angle": "string",
      "top_hooks": ["string"],
      "best_platform": "string",
      "best_posting_time": "string"
    }
  ]
}
```

## Dependencies
- Memory Agent
- Analytics Agent
- ChromaDB
- Database (knowledge table)
