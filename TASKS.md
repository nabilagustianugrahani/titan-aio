# TITAN AIO — Tasks

## Legend
- `[x]` Done
- `[~]` In Progress
- `[ ]` Pending

---

## Phase 1 — MVP

### Infrastructure
- [x] Initialize Python 3.11+ project with `pyproject.toml`
- [x] Set up FastAPI + FastMCP server skeleton
- [x] Configure Redis queue connection
- [x] Configure PostgreSQL connection (asyncpg)
- [x] Configure ChromaDB vector store
- [x] Set up S3-compatible storage client
- [x] Dockerize development environment

### MCP Tools
- [x] Implement `health()` tool
- [x] Implement `search_product()` tool
- [x] Implement `analyze_product()` tool
- [x] Implement `analyze_reviews()` tool
- [x] Implement `analyze_competitors()` tool
- [x] Implement `generate_hooks()` tool
- [x] Implement `generate_script()` tool
- [x] Implement `generate_thumbnail()` tool
- [x] Implement `generate_image()` tool
- [x] Implement `create_affiliate_package()` tool

### Agents (MVP)
- [x] Build base agent class with DI
- [x] Build **Product Agent** — scrape & analyze Shopee/Tokopedia URLs
- [x] Build **Review Agent** — extract pain points, objections, benefits from reviews
- [x] Build **UGC Agent** — generate 10 hooks + 10 scripts per product
- [x] Build **Creative Agent** — thumbnail concepts + shot lists

### Generation
- [x] Wire Generation Router to dispatch image jobs
- [x] Implement S3 upload from worker

### Orchestration
- [x] Build **CEO Agent** — LangGraph workflow for MVP
- [x] Wire URL input → Product → Review → UGC → Creative → Image pipeline
- [x] Return complete affiliate package as output

---

## Phase 2 — Intelligence

### Agents
- [x] Build **Trend Agent** — detect trending products & opportunities
- [x] Build **Competitor Agent** — analyze competitor ads & hooks
- [x] Build **Memory Agent** — persist winning/failed campaign data
- [x] Build **Analytics Agent** — CTR, conversion, revenue tracking

### Database
- [x] Design and migrate PostgreSQL schema (all tables)
- [x] Implement ChromaDB vector memory for winning hooks/products
- [x] Implement campaign save/load from database

### MCP Tools (Phase 2)
- [x] Implement `save_campaign()` tool
- [x] Implement `load_campaign()` tool
- [x] Implement `get_metrics()` tool
- [x] Implement `get_recommendations()` tool

---

## Phase 3 — Video & Avatars

### Agents
- [x] Build **Video Agent** — short-form video generation
- [x] Build **Avatar Agent** — AI spokesperson with character consistency

### Generation
- [x] Implement LoRA policy (train only if usage_count > 20)
- [x] Implement reference-image fallback for low-usage products

### MCP Tools (Phase 3)
- [x] Implement `generate_video()` tool
- [x] Implement `generate_avatar()` tool

---

## Phase 4 — Scale & Automate

### Agents
- [x] Build **Publisher Agent** — platform formatting & scheduling
- [x] Build **Finance Agent** — revenue, commission, ROI tracking
- [x] Build **Growth Agent** — auto-scale winners, kill losers
- [x] Integrate all agents under CEO Agent orchestration

### MCP Tools (Phase 4)
- [x] Wire full `create_affiliate_package()` for all phases

---

## Cross-Cutting

- [x] Write test suite (unit + integration) — 67/67 passing
- [x] Document every module (AGENTS/ + .titan/)
- [x] Create Kaggle notebook template
- [x] Set up CI/CD pipeline
- [x] Performance benchmark: end-to-end package generation time

---

## 🔄 Needs Human Action

| # | Task | Est. Time |
|---|------|-----------|
| 1 | **Register Shopee/Tokopedia Affiliate Account** — get API keys → add to `.env` | 30 min |
| 4 | ~~**Set up Notion Dashboard**~~ — ✅ Done (3 databases configured) | — |
| 5 | ~~**Deploy to Production VPS**~~ — ✅ Done (systemd service active, port 8080) | — |
| 6 | **Run Real Campaign Test** — real URL → publish → measure ROI (blocked by #3: Shopee/Tokopedia keys) | 1 hr |
