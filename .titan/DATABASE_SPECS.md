# TITAN AIO — Database Specifications

## Connection
- **Engine**: SQLAlchemy 2.0 async
- **Driver**: asyncpg (prod) / aiosqlite (dev/test)
- **Session**: `async_session_factory` → per-request sessions
- **Base**: DeclarativeBase with `extend_existing=True` for hot-reload safety

## Schema

### Tables (14)

| Table | Key Fields | Purpose |
|-------|-----------|---------|
| `products` | id, external_id, title, price, rating, sales, category, commission, competition, url, usage_count | Source product data |
| `reviews` | id, product_id, text, rating, sentiment, category, pain_points | Review intelligence |
| `campaigns` | id, product_id, name, status, platform, budget, spent, revenue, config | Campaign management |
| `affiliate_links` | id, campaign_id, platform, url, clicks, conversions | Link tracking |
| `generated_assets` | id, campaign_id, asset_type, url, model_used, metadata | Asset registry |
| `winning_hooks` | id, campaign_id, hook_text, hook_type, ctr, embedding | Hook library |
| `winning_products` | id, product_id, category, total_revenue, roi | Product library |
| `winning_cta` | id, campaign_id, cta_text, conversion_rate | CTA library |
| `failed_campaigns` | id, campaign_id, product_id, reason, metrics_snapshot | Failure analysis |
| `metrics` | id, campaign_id, platform, views, clicks, ctr, conversions, revenue, period | Campaign metrics |
| `knowledge` | id, category, pattern, confidence, evidence, advice, embedding | Knowledge base |
| `avatar_profiles` | id, name, persona, character_sheet, generation_params, base_image | Avatar registry |
| `product_profiles` | id, product_id, score, summary, review_intel, competitor_intel, offer | Product profiles |

### Indices
- All `id` columns: primary key
- All `external_id`, `campaign_id`, `product_id`: unique or b-tree index
- `winning_hooks.embedding`, `knowledge.embedding`: for vector search (ChromaDB companion)

## Repository Pattern
```python
class Repository(ModelT):
    async def create(**kwargs) -> ModelT
    async def get(id) -> ModelT | None
    async def find(**filters) -> list[ModelT]
    async def update(id, **kwargs) -> ModelT | None
    async def delete(id) -> bool
    async def list_all(limit, offset) -> list[ModelT]
```

## Migration Strategy
- Dev: SQLAlchemy `create_all()` on startup (safe with `extend_existing`)
- Prod: Alembic (to be added in Phase 2)
