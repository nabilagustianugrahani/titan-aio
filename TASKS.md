# TITAN AIO — Tasks

## Legend
- `[ ]` Pending
- `[~]` In Progress
- `[x]` Done

---

## Phase 1 — MVP

### Infrastructure
- [ ] Initialize Python 3.11+ project with `pyproject.toml`
- [ ] Set up FastAPI + FastMCP server skeleton
- [ ] Configure Redis queue connection
- [ ] Configure PostgreSQL connection (asyncpg)
- [ ] Configure ChromaDB vector store
- [ ] Set up S3-compatible storage client
- [ ] Dockerize development environment

### MCP Tools
- [ ] Implement `health()` tool
- [ ] Implement `search_product()` tool
- [ ] Implement `analyze_product()` tool
- [ ] Implement `analyze_reviews()` tool
- [ ] Implement `analyze_competitors()` tool
- [ ] Implement `generate_hooks()` tool
- [ ] Implement `generate_script()` tool
- [ ] Implement `generate_thumbnail()` tool
- [ ] Implement `generate_image()` tool
- [ ] Implement `create_affiliate_package()` tool

### Agents (MVP)
- [ ] Build base agent class with DI
- [ ] Build **Product Agent** — scrape & analyze Shopee/Tokopedia URLs
- [ ] Build **Review Agent** — extract pain points, objections, benefits from reviews
- [ ] Build **UGC Agent** — generate 10 hooks + 10 scripts per product
- [ ] Build **Creative Agent** — thumbnail concepts + shot lists

### Generation
- [ ] Set up Kaggle image-worker with FLUX Schnell
- [ ] Set up Kaggle image-worker with FLUX Dev
- [ ] Wire Generation Router to dispatch image jobs
- [ ] Implement S3 upload from Kaggle worker

### Orchestration
- [ ] Build **CEO Agent** — LangGraph workflow for MVP
- [ ] Wire URL input → Product → Review → UGC → Creative → Image pipeline
- [ ] Return complete affiliate package as output

---

## Phase 2 — Intelligence

### Agents
- [ ] Build **Trend Agent** — detect trending products & opportunities
- [ ] Build **Competitor Agent** — analyze competitor ads & hooks
- [ ] Build **Memory Agent** — persist winning/failed campaign data
- [ ] Build **Analytics Agent** — CTR, conversion, revenue tracking

### Database
- [ ] Design and migrate PostgreSQL schema (all tables)
- [ ] Implement ChromaDB vector memory for winning hooks/products
- [ ] Implement campaign save/load from database

### MCP Tools (Phase 2)
- [ ] Implement `save_campaign()` tool
- [ ] Implement `load_campaign()` tool
- [ ] Implement `get_metrics()` tool
- [ ] Implement `get_recommendations()` tool

---

## Phase 3 — Video & Avatars

### Agents
- [ ] Build **Video Agent** — short-form video generation
- [ ] Build **Avatar Agent** — AI spokesperson with character consistency

### Generation
- [ ] Set up Kaggle video-worker with Wan 2.2
- [ ] Set up Kaggle video-worker with Hunyuan Video
- [ ] Set up Kaggle lora-worker with Kohya/SimpleTuner
- [ ] Implement LoRA policy (train only if usage_count > 20)
- [ ] Implement reference-image fallback for low-usage products

### MCP Tools (Phase 3)
- [ ] Implement `generate_video()` tool
- [ ] Implement `generate_avatar()` tool

---

## Phase 4 — Scale & Automate

### Agents
- [ ] Build **Publisher Agent** — platform formatting & scheduling
- [ ] Build **Finance Agent** — revenue, commission, ROI tracking
- [ ] Build **Growth Agent** — auto-scale winners, kill losers
- [ ] Integrate all agents under CEO Agent orchestration

### MCP Tools (Phase 4)
- [ ] Wire full `create_affiliate_package()` for all phases

---

## Cross-Cutting

- [ ] Set up CI/CD pipeline
- [ ] Write test suite (unit + integration)
- [ ] Document every module
- [ ] Create Kaggle notebook template (already scaffolded)
- [ ] Performance benchmark: end-to-end package generation time
