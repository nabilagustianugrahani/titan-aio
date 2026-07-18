# Memory Agent

## Role
Campaign historian — persists and retrieves campaign knowledge.

## Responsibilities
Store:
- Winning Hooks
- Winning Products
- Winning CTA
- Winning Campaigns
- Failed Campaigns

## Storage Layers
1. **Structured DB** (PostgreSQL) — campaign data, metrics
2. **Vector Store** (ChromaDB) — embeddings for semantic retrieval

## Input
- Campaign results (from Analytics Agent)
- Winning creative data
- User feedback

## Processing
1. Classify campaign as winning or failed
2. Extract winning elements (hooks, CTAs, thumbnails, creatives)
3. Store embeddings in vector DB for similarity search
4. Update knowledge base with new learnings

## Output: Knowledge Storage
```json
{
  "campaign_id": "string",
  "stored_elements": {
    "hooks_stored": 0,
    "products_stored": 0,
    "ctas_stored": 0,
    "creatives_stored": 0
  },
  "classification": "winning | failed | learning"
}
```

## Query Interface
- `find_similar_hooks(query_text, top_k=5)`
- `find_winning_products(category, top_k=10)`
- `get_best_posting_times(platform)`
- `get_failed_patterns(category)`

## Dependencies
- ChromaDB vector store
- Database (winning_hooks, winning_products, winning_cta, failed_campaigns)
- Knowledge Agent
