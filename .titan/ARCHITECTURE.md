# TITAN AIO — Architecture

## System Diagram

```
User
  │
  ▼
Titan MCP (FastMCP :8080)
  │
  ▼
CEO Agent (orchestrator)
  │
  ├──► Product Agent
  ├──► Review Agent
  ├──► UGC Agent
  ├──► Creative Agent
  ├──► Offer Agent
  ├──► Trend Agent
  ├──► Competitor Agent
  ├──► Memory Agent
  ├──► Analytics Agent
  ├──► Video Agent
  ├──► Avatar Agent
  ├──► Publisher Agent
  ├──► Finance Agent
  └──► Growth Agent
  │
  ▼
Generation Router (Redis)
  │
  ├──► Kaggle image-worker (FLUX T4)
  ├──► Kaggle video-worker (Wan 2.2 T4)
  └──► Kaggle lora-worker (Kohya T4)
  │
  ▼
S3 Storage ──► Affiliate Package
```

## Layer Architecture

```
┌────────────────────────────────────────────┐
│            MCP Layer (FastMCP)              │
│  ┌────────────────────────────────────┐    │
│  │  Tool Layer (22 MCP tools)          │    │
│  └────────────┬───────────────────────┘    │
├───────────────┼────────────────────────────┤
│  Agent Layer  │  CEO Orchestrator          │
│  ┌────────────▼───────────────┐            │
│  │ 16 Specialized Agents      │            │
│  └────────────────────────────┘            │
├────────────────────────────────────────────┤
│  Service Layer                              │
│  ┌──────────────┐ ┌──────────────────┐     │
│  │ Memory       │ │ Knowledge Base   │     │
│  │ (ChromaDB)   │ │ (Vector Store)   │     │
│  └──────────────┘ └──────────────────┘     │
├────────────────────────────────────────────┤
│  Data Layer                                 │
│  ┌──────────────┐ ┌──────────────────┐     │
│  │ PostgreSQL   │ │ Redis Queue      │     │
│  │ (asyncpg)    │ │ (Generation)     │     │
│  └──────────────┘ └──────────────────┘     │
├────────────────────────────────────────────┤
│  Worker Layer                               │
│  ┌──────────────┐ ┌──────────────────┐     │
│  │ Kaggle T4    │ │ S3 Storage       │     │
│  │ (FLUX/Wan)   │ │ (Assets)         │     │
│  └──────────────┘ └──────────────────┘     │
└────────────────────────────────────────────┘
```

## Data Flow (MVP)

```
URL Input
  → Product Agent scrapes & analyzes
  → Review Agent extracts intelligence
  → Competitor Agent finds gaps
  → Offer Agent positions product
  → UGC Agent generates hooks + scripts
  → Creative Agent designs thumbnails
  → Generation Router → Kaggle → images
  → Compile Affiliate Package → Return
```

## Key Design Decisions
- **No business logic in Kaggle** — workers only run models
- **CEO Agent never generates** — pure orchestrator
- **FastMCP tools map 1:1 to capabilities** — thin wrappers over agents
- **Repository pattern** — consistent data access
- **ChromaDB for semantic search** — winning hooks, products, CTAs
- **SQLite for dev, PostgreSQL for prod** — env switch via DATABASE_URL
