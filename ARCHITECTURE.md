# TITAN AIO — Architecture

## System Overview

Titan AIO is orchestrated by a **CEO Agent** that routes work through specialized sub-agents and dispatches generation tasks to **Kaggle Workers** via a **Generation Router**.

```
┌─────────────┐
│    User     │  (Affiliate URL input)
└──────┬──────┘
       │
┌──────▼──────┐
│  Titan MCP  │  (FastMCP server — entry point)
└──────┬──────┘
       │
┌──────▼──────┐
│ CEO Agent   │  (CrewAI + LangGraph orchestrator)
└──────┬──────┘
       │
       ├──────────────────────────────────────────────┐
       │                                              │
       ▼                                              ▼
┌──────────────┐                            ┌──────────────────┐
│ Core Agents  │                            │ Support Agents   │
│              │                            │                  │
│ Product      │                            │ Memory           │
│ Review       │                            │ Knowledge        │
│ Competitor   │                            │ Analytics        │
│ Offer        │                            │ Finance          │
│ UGC          │                            │ Growth           │
│ Creative     │                            │                  │
│ Avatar       │                            │                  │
│ Video        │                            │                  │
│ Publisher    │                            │                  │
│ Trend        │                            │                  │
└──────┬───────┘                            └──────────────────┘
       │
       │  Generation tasks dispatched via Redis queue
       ▼
┌──────────────────────────────────────────────────┐
│              Generation Router                    │
│  (Load balancer — route to available Kaggle)     │
└────┬─────────┬──────────┬────────────────────────┘
     │         │          │
     ▼         ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐
│ Image  │ │ Video  │ │ LoRA   │
│ Worker │ │ Worker │ │ Worker │
└────────┘ └────────┘ └────────┘
(Kaggle T4) (Kaggle T4) (Kaggle A100)
```

---

## Data Flow

### Request Flow (Synchronous)
```
User URL
  → MCP Tool Call
  → CEO Agent plans workflow
  → Product Agent fetches & analyzes
  → Review Agent scrapes reviews
  → UGC Agent generates scripts
  → Creative Agent designs visuals
  → Generation Router submits jobs
  → Return affiliate package
```

### Generation Flow (Async via Redis)
```
Creative Agent submits job
  → Generation Router enqueues to Redis
  → Kaggle Worker polls Redis
  → Worker runs FLUX / Wan / Kohya
  → Worker uploads result to S3
  → Generation Router updates job status
  → CEO Agent collects results
```

---

## Component Architecture

### FastMCP Server (`/mcp/`)
```
mcp/
├── server.py              # FastMCP app, tool registration
├── tools/
│   ├── health.py
│   ├── search_product.py
│   ├── analyze_product.py
│   ├── analyze_reviews.py
│   ├── analyze_competitors.py
│   ├── generate_offer.py
│   ├── generate_hooks.py
│   ├── generate_script.py
│   ├── generate_thumbnail.py
│   ├── generate_image.py
│   ├── generate_video.py
│   ├── generate_avatar.py
│   ├── create_affiliate_package.py
│   ├── save_campaign.py
│   ├── load_campaign.py
│   ├── get_metrics.py
│   └── get_recommendations.py
├── schemas/
│   └── ...                 # Pydantic models for tool I/O
└── dependencies.py         # DI container
```

### Agent Framework (`/services/`)
```
services/
├── orchestrator.py         # CEO Agent — LangGraph workflow
├── agents/
│   ├── base.py             # Abstract base agent
│   ├── trend.py
│   ├── product.py
│   ├── review.py
│   ├── competitor.py
│   ├── offer.py
│   ├── ugc.py
│   ├── creative.py
│   ├── avatar.py
│   ├── video.py
│   ├── publisher.py
│   ├── analytics.py
│   ├── memory.py
│   ├── knowledge.py
│   ├── finance.py
│   └── growth.py
└── memory/
    ├── vector_store.py     # ChromaDB client
    └── knowledge_base.py   # Knowledge retrieval
```

### Generation Router (`/workers/`)
```
workers/
├── router.py               # Redis-based job dispatcher
├── image_worker.py         # FLUX Schnell / FLUX Dev
├── video_worker.py         # Wan 2.2 / Hunyuan Video
└── lora_worker.py          # Kohya / SimpleTuner
```

### Database (`/database/`)
```
database/
├── models/
│   ├── product.py
│   ├── review.py
│   ├── campaign.py
│   ├── affiliate_link.py
│   ├── generated_asset.py
│   ├── winning_hook.py
│   ├── winning_product.py
│   ├── winning_cta.py
│   ├── failed_campaign.py
│   ├── metric.py
│   ├── knowledge.py
│   ├── avatar_profile.py
│   └── product_profile.py
├── migrations/
│   └── ...
├── connection.py           # Async PG connection
└── repository.py           # Generic CRUD base
```

---

## Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| API Framework | FastAPI | Async, auto-docs, Pydantic validation |
| MCP | FastMCP | Native MCP protocol support for Claude |
| Agent Orchestration | CrewAI + LangGraph | CrewAI for agent roles, LangGraph for stateful workflows |
| Vector Store | ChromaDB | Lightweight, local, no separate server |
| Queue | Redis | Simple, fast, widely supported |
| Storage | S3-compatible | Scalable, cheap, standard API |
| Image Gen | FLUX Schnell/Dev | Fast, open, quality output |
| Video Gen | Wan 2.2 / Hunyuan | Open models, good short-form quality |
| LoRA Training | Kohya / SimpleTuner | Mature tooling for product fine-tuning |
| GPU Workers | Kaggle (T4/A100) | Free tier for generation, usage-based |

---

## Security & Isolation

- Kaggle workers run **only generation code** — no business logic, no API keys for affiliate networks.
- All secrets (API keys, DB credentials) stored in environment variables, never in code.
- MCP tools validate input at schema layer.
- S3 access via signed URLs with expiration.
