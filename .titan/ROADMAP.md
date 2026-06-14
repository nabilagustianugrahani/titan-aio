# TITAN AIO — ROADMAP

## Phase 1 — MVP (Complete)
**Goal:** Functioning affiliate intelligence pipeline from URL to package.

All deliverables shipped and verified.

### Deliverables
- [x] Project scaffold (directories, config, pyproject.toml)
- [x] Database layer (connection, models, repository)
- [x] Pydantic schemas (all I/O models)
- [x] FastMCP server with all tools registered (30 tools)
- [x] Product Agent — scrape & analyze product URL
- [x] Review Agent — extract pain points, objections, benefits
- [x] UGC Agent — generate 10 hooks + 10 scripts
- [x] Creative Agent — thumbnail concept + shot lists
- [x] Image Generation — FLUX pipeline via Kaggle worker
- [x] Full pipeline: URL → affiliate package
- [x] 71 tests, 70 passing across 9 test files
- [x] Notion API integration active

### Acceptance Criteria
```
Input:  URL → Output: Product Analysis + Review Summary + 10 Hooks + 10 Scripts + Thumbnail + Image
```

---

## Phase 2 — Intelligence (In Progress)
**Goal:** Add competitive awareness and persistent memory.

Phase 2 tool implementations built and registered on MCP server. Remaining work: real data feeds and production tuning.

### Deliverables
- [x] Trend Agent — detect trending products & market shifts
- [x] Competitor Agent — analyze competitor ads & hooks
- [x] Memory Agent — persist winning/failed campaign data
- [x] Analytics Agent — track CTR, conversions, revenue
- [x] ChromaDB integration for vector memory
- [x] PostgreSQL schema migration for campaigns & metrics
- [ ] Trend data pipeline with real market feeds
- [ ] ChromaDB production tuning & indexing

---

## Phase 3 — Video & Avatars (Not Started)
**Goal:** Full multimedia generation pipeline.

Tool stubs and agent specs exist; implementation deferred.

### Deliverables
- [ ] Video Agent — short-form video generation (Wan 2.2 / Hunyuan)
- [ ] Avatar Agent — AI spokesperson with consistent character
- [ ] Product LoRA training pipeline (Kohya/SimpleTuner)
- [ ] LoRA policy enforcement (train only if usage_count > 20)
- [ ] Kaggle video-worker deployed on T4

---

## Phase 4 — Scale & Automate (Not Started)
**Goal:** Autonomous campaign lifecycle management.

### Deliverables
- [ ] Publisher Agent — auto-format & schedule to platforms
- [ ] Finance Agent — revenue, commission, ROI tracking
- [ ] Growth Agent — auto-scale winners, kill losers
- [ ] Full agent orchestration via CEO Agent
- [ ] Dashboard for campaign performance

---

## Guiding Principles
1. **Revenue first** — every phase must unblock revenue generation.
2. **No premature optimization** — build what's needed now.
3. **Iterate fast** — ship MVP, then layer intelligence.
4. **Kaggle is infra** — never put business logic in workers.
5. **Data is equity** — every campaign enriches the knowledge base.
