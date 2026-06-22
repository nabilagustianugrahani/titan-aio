# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Titan AIO is an autonomous affiliate intelligence system. Input: a Shopee/Tokopedia product URL. Output: a complete affiliate campaign (product analysis, hooks, scripts, images, video, captions) synced to Notion dashboard and Google Drive.

## Commands

```bash
# Quick start (VPS: Python 3.11, 859MB RAM)
./run.sh                # run tests
./run.sh serve          # start server at :8080
./run.sh dashboard      # same as serve
./run.sh launch <url>   # autonomous campaign (single mode)
./run.sh loop           # continuous autonomous mode
./run.sh mcp            # MCP stdio for Claude Code
./run.sh dbs <page_id>  # setup Notion databases
./run.sh install        # reinstall deps

# Or directly:
python -m pytest Tests/ -v                              # all tests
python -m pytest Tests/ -v -k "test_health"             # single test
python -m pytest Tests/test_mcp_tools.py -v             # single file
python -m titan.main                                    # server at :8080
python MCP/standalone.py                                # MCP stdio
python -m Services.notion.setup_dbs <parent_page_id>    # Notion DBs
python titan/autonomous_loop.py --mode once             # single cycle
python titan/autonomous_loop.py --mode continuous --interval 30  # continuous
python -m titan.launch <url>                            # one-shot launch
python -m titan.launch <url> --mode batch --variants 3  # A/B testing
python -m titan.launch <url> --mode lip-sync --face-image face.jpg
python Tests/benchmark.py                               # performance benchmark

# Lint & Typecheck
ruff check .
mypy Services/agents/ --ignore-missing-imports --no-error-summary || true

# MCP registration
claude mcp add titan-aio -- python MCP/standalone.py
# Or with env file:
claude mcp add titan-aio --env-file .env -- python MCP/standalone.py
```

**Package manager:** Use `uv` (not pip) when available. `run.sh` auto-creates venv with uv.

**Env var note:** `run.sh` sets `PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python` to avoid protobuf issues.

## Architecture

```
User URL → MCP Server (FastMCP, 48 tools) → CEO Agent (orchestrator)
  → Core Pipeline: Product → Review → Offer → UGC → Creative → Image/Video
  → Intelligence: Trend, Competitor, Memory, Analytics, Finance, Growth
  → Media: Video Agent, Avatar Agent, LoRA Pipeline
  → Output: Notion Dashboard + Google Drive + MongoDB Atlas
```

**Three orchestration paths:**
1. **CEO Agent** (`Services/orchestrator.py`): sequential agent calls via `create_affiliate_package()`, publishes events to MessageBus
2. **LangGraph** (`Services/graph_workflow.py`): state graph with parallel fan-out (reviews ‖ competitors), conditional branching, self-healing retries (MAX_RETRIES=3, 2s exponential backoff), telemetry per node
3. **Autonomous Pipeline** (`Services/autonomous_pipeline.py`): end-to-end flow with video generation, lip sync, auto-publish to 6 platforms

**Key pattern — MCP tool → Core function:**
- `MCP/tools/*.py` are thin wrappers (Pydantic validation + delegation)
- Real logic lives in `Services/agents/` and `Services/` modules
- Every tool function is `async`, takes a Pydantic input model, returns a Pydantic output model
- Tool functions that need DB manage their own sessions via `get_session()` async generator (see `MCP/tools/analyze_product.py`)
- Pydantic schemas centralized in `MCP/schemas/__init__.py`

**Agent pattern:**
- All agents extend `BaseAgent` from `Services/agents/base.py`
- `BaseAgent.__call__` handles DB session lifecycle: create → execute → rollback on error → close (always)
- Agents receive `AgentContext(session=AsyncSession)` — never create their own sessions
- `BaseAgent.__call__` creates the session automatically; agents only implement `execute(ctx, **kwargs)`

**Agent communication — MessageBus** (`Services/agents/message_bus.py`):
- Zero-deps in-memory pub/sub, singleton via `get_bus()`
- `publish(event_type, data, source)` → broadcasts to all handlers, stores last 1000 events (trims to 500)
- `subscribe(event_type, handler)` → register callback for event type
- `get_latest(event_type)` → get most recent event data (used by agents to read latest state)
- `get_history(event_type, limit)` → replay past events
- Event types: `trends.analyzed`, `reviews.analyzed`, `competitors.analyzed`, `offer.created`, `content.generated`, `graph.optimize`, `product.analyzed`, `video.generated`, `campaign.created`
- Used for pipeline orchestration: CEO Agent publishes, downstream agents subscribe

**Database:**
- SQLAlchemy async with `async_session_factory`. SQLite dev, MongoDB Atlas prod.
- UUID PKs in `Database/models/`
- `Repository[ModelT]` generic CRUD: `create(**kwargs)`, `get(id)`, `find(**filters)`, `update(id, **kwargs)`, `delete(id)`
- `Database/connection.py` provides `get_session()` (async generator for FastAPI DI), `init_db()` (CREATE IF NOT EXISTS), `close_db()`

**Config:** `titan/config.py` — pydantic-settings loading from `.env`. Template at `.env.example`. All secrets in `.env` only.

**Error handling:**
- `BaseAgent.__call__`: try/execute → rollback on error → close session (always)
- LangGraph `run_node`: MAX_RETRIES=3, exponential backoff (2s base), telemetry per node
- `optimize_hooks`: up to 3 rounds of hook regeneration for low-CTR hooks
- Phase state machine: DISCOVER → ANALYZE → CREATE → OPTIMIZE → PUBLISH → COMPLETE/FAILED

## Environment Variables

Required (`.env` or exported):
```
DATABASE_URL=sqlite+aiosqlite:///./data/titan.db   # default SQLite dev
NOTION_TOKEN=                                       # Notion API
NOTION_CAMPAIGN_DB=                                 # Notion database IDs
NOTION_KNOWLEDGE_DB=
NOTION_TASKS_DB=
MONGODB_URI=                                        # MongoDB Atlas
MONGODB_DB_NAME=titan_aio
GDRIVE_CREDENTIALS_FILE=./credentials/gdrive.json
GDRIVE_FOLDER_ID=
HF_TOKEN=                                           # HuggingFace (for Modal GPU workers)
SCRAPINGBEE_API_KEY=                                # Cloud browser scraping
```

Optional: `REDIS_URL`, `S3_ENDPOINT/ACCESS_KEY/SECRET_KEY/BUCKET`, `MONGODB_PUBLIC_KEY/PRIVATE_KEY/PROJECT_ID`, `CHROMA_PERSIST_DIR`, `HOST`, `PORT`, `LOG_LEVEL`.

## Platform Publishing

6 platforms with per-platform formatting + anti-shadowban:

| Platform | Max Chars | CTA Style |
|----------|-----------|-----------|
| TikTok | 300 | "Link di bio! 👆" |
| Instagram | 2200 | "Link di bio! 🔗" |
| Facebook | 63206 | "Order sekarang! Link di komentar." |
| YouTube | — | Title + description |
| Twitter | 280 | "Link di bio! 🔗" |
| Shopee | — | Product listing format |

**Anti-shadowban** (`Services/publisher/anti_shadowban.py`):
- Random delays: 2-4h (new), 1-2h (growing), 30-90min (established), ±30% jitter
- Daily limits: 2 (warming), 4 (growing), 8 (established)
- Content ratio: 30% affiliate, 70% organic
- Hashtag rotation by category (elektronik/fashion/umum), 3 sets per category
- Affiliate disclosure injected randomly (`*affiliate` or `#ad`)

**Flow:** Caption → AntiShadowban (rotate hashtags + add disclosure) → Platform formatter (char limit + CTA) → BrowserUse auto-upload with saved sessions

## Video & Image Pipeline

GPU work runs on **Modal** workers (never on VPS):

| Model | Task | GPU | Timeout |
|-------|------|-----|---------|
| FLUX.1-schnell | Image generation | A100 | 900s |
| SD 3.5 Medium | Image generation | T4 | 600s |
| Wan 2.2 T2V-A14B | Video generation | A100 | 900s |
| Google Veo 2 | Video generation (API) | — | — |

**Dispatch pattern:**
- `Workers/modal_a100.py` → `@app.function(gpu="A100")` for FLUX & Wan 2.2
- `Workers/modal_image.py` → `@app.function(gpu="T4")` for SD 3.5
- `Services/video/google_flow.py` → Google Veo 2 API client (safe for VPS, no memory issues)
- `Services/video/vimax_adapter.py` → ViMax multi-shot adapter
- `Services/video/lip_sync.py` → Wav2Lip (primary), SadTalker (fallback), Wan native (no face)
- `Services/video/variant_generator.py` → A/B batch variant generation

**UGC flow:** `Services/ugc/engine.py` generates AI video prompts (Gemini 2.5 Flash) → Worker dispatches to GPU → Download results → Assembly

**Model cache:** `Services/gdrive/model_store.py` caches FLUX/Wan models in GDrive (5-30GB) to avoid redownloading.

## API Endpoints (`titan/main.py`)

```
GET  /                        → App info
GET  /health                  → Health check
GET  /dashboard               → HTML dashboard (Jinja2)
GET  /api/dashboard/stats     → Revenue, campaigns, knowledge stats
GET  /api/dashboard/chart     → 7-day revenue time-series
POST /api/dashboard/refresh   → Refresh cached data
POST /api/run/cycle           → Trigger autonomous campaign cycle
```

Dashboard at `http://localhost:8080/dashboard` — revenue chart, stats cards, campaign table, auto-refresh 30s.

## Data Model

Key entities in `Database/models/` (all UUID PKs):

- **Campaign** → has many: Product, WinningHook, WinningCTA, FailedCampaign, Metric, AffiliateLink, GeneratedAsset
- **Product** → has many: Review, Campaign; has one: ProductProfile
- **Review** → belongs to Product; fields: rating, sentiment, pain_points, quotes
- **WinningHook** → belongs to Campaign; fields: hook_text, ctr, embedding
- **WinningCTA** → belongs to Campaign; fields: cta_text, conversion_rate
- **KnowledgeEntry** → learned patterns from successful campaigns
- **AvatarProfile** → character profiles for AI spokesperson
- **Metric** → per-campaign performance data

Connection: `Database/connection.py` → `async_session_factory` (SQLite dev / MongoDB Atlas prod)

## Structure

```
MCP/                    FastMCP server + 26 tool modules + Pydantic schemas (48 tools total)
Services/agents/        20 agents + BaseAgent + MessageBus
Services/orchestrator.py  CEO Agent — imports and coordinates all agents
Services/graph_workflow.py  LangGraph state graph (DISCOVER→ANALYZE→CREATE→PUBLISH)
Services/autonomous_pipeline.py  Full autonomous pipeline with video + publish
Services/notion/        Notion API client + dashboard sync (3 databases)
Services/mongodb/       MongoDB Atlas client + Atlas Admin API
Services/gdrive/        Google Drive 5TB + model store
Services/memory/        ChromaDB vector store for hooks/products
Services/publisher/     BrowserUse auto-upload + anti-shadowban engine
Services/video/         Video generation (Google Veo 2, ViMax, lip sync)
Workers/                Modal GPU workers (A100/T4)
Database/               SQLAlchemy async connection + ORM models + repository (Generic CRUD)
titan/                  FastAPI app, autonomous loop, launch controller, config
Tests/                  12 test files, 66 tests + benchmark tool
AGENTS/                 17 agent specification docs
```

**20 Agents** (`Services/agents/`):
Core pipeline: `product`, `review`, `content`, `offer`, `scraper`
Intelligence: `trend`, `competitor`, `analytics`, `knowledge`, `memory`
Media: `video`, `avatar`, `asset`
Operations: `publisher`, `antishadowban`, `commission_hunter`, `affiliate`, `campaign_builder`
Finance: `finance`, `growth`
Infrastructure: `base` (BaseAgent ABC), `message_bus` (pub/sub)

## CI/CD

GitHub Actions on push/PR to `main`:
- **lint**: `ruff check .`
- **test**: `pytest Tests/ -v --tb=short`
- **typecheck**: `mypy Services/agents/ --ignore-missing-imports || true`
- **docker**: build image on main push (after lint+test pass)

## Testing

- Tests use SQLite `test.db` (auto-created, seeded with 5 products, 2 metrics, 3 hooks)
- `conftest.py` sets `DATABASE_URL` before any imports — no real DB needed
- Use `@pytest.mark.asyncio` for async tests
- Run benchmark: `python Tests/benchmark.py [--repeat N] [--json]`

## Development Rules

- Typed Python: every function annotated with return types
- Async first: no blocking I/O in agent/tool code
- GPU workers = generation only, no business logic, no API keys
- Secrets in `.env` (gitignored), never in code
- DI pattern: agents get sessions via `AgentContext`, singletons only for `config.settings`
- MCP tool files are thin: validate input → call core function → return output
- Tools that manage their own DB sessions use `get_session()` async generator (see `analyze_product.py`)
- Agents that extend `BaseAgent` get sessions auto-managed — just implement `execute(ctx, **kwargs)`

## VPS Rules (CRITICAL — LOW MEMORY 859MB RAM)

**DO NOT install heavy packages on VPS:**
- ❌ torch, pytorch, tensorflow
- ❌ diffusers, transformers, accelerate
- ❌ opencv-python, moviepy, imageio
- ❌ sentencepiece, protobuf (heavy)
- ❌ any ML/AI/GPU library

**VPS is for lightweight code only:**
- ✅ httpx, aiohttp (HTTP requests)
- ✅ Pillow (image processing, <50MB)
- ✅ SQLAlchemy, pydantic (database)
- ✅ fastmcp, fastapi (API server)

**GPU work goes to remote workers:**
- Generate `.ipynb` notebook → upload to worker → run there
- Download output → upload to server
- Never run GPU tasks on VPS

**If you need to install something:**
1. Check if it's lightweight (<50MB)
2. Check if it can run on remote GPU worker instead
3. Ask user first if unsure
