# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Titan AIO is an autonomous affiliate intelligence system. Input: a Shopee/Tokopedia product URL. Output: a complete affiliate campaign (product analysis, hooks, scripts, images, video, captions) synced to Notion dashboard and Google Drive.

## Commands

```bash
# Environment (requires Python 3.11+)
pip install -e ".[dev]"                    # install all deps
~/.local/bin/micromamba run -n titan ...   # or use conda env "titan"

# Tests (67 tests, all must pass)
python -m pytest Tests/ -v                 # run all
python -m pytest Tests/test_agents.py -v   # run single file
python -m pytest -k "test_health" -v       # run single test

# Server
python -m titan.main                       # FastAPI dashboard at :8080
python MCP/standalone.py                   # MCP stdio for Claude Code

# Pipeline
python titan/autonomous_loop.py --mode once                    # single cycle
python titan/autonomous_loop.py --mode continuous --max-cycles 0  # continuous
python -m titan.launch <product-url>                           # one-shot launch

# MCP registration
claude mcp add titan-aio -- python MCP/standalone.py
```

## Architecture

```
User URL → MCP Server (FastMCP, 48 tools) → CEO Agent (orchestrator)
  → Core Pipeline: Product → Review → Offer → UGC → Creative → Image/Video
  → Intelligence: Trend, Competitor, Memory, Analytics, Finance, Growth
  → Media: Video Agent, Avatar Agent, LoRA Pipeline
  → Output: Notion Dashboard + Google Drive + MongoDB Atlas
```

**Two pipeline paths:**
1. **Synchronous** (`create_affiliate_package`): sequential tool calls, returns full package
2. **LangGraph** (`graph_workflow.py`): state graph with parallel fan-out, conditional branching, self-healing retries, telemetry

**Key pattern — MCP tool → Core function:**
- `MCP/tools/*.py` are thin wrappers (Pydantic validation + delegation)
- Real logic lives in `Services/agents/` and `Services/` modules
- Every tool function is `async`, takes a Pydantic input model, returns a Pydantic output model

**Agent pattern:**
- All agents extend `BaseAgent` from `Services/agents/base.py`
- `BaseAgent.__call__` handles DB session lifecycle (create → execute → rollback on error → close)
- Agents receive `AgentContext(session=AsyncSession)` — never create their own sessions
- `MessageBus` (`Services/agents/message_bus.py`) for inter-agent events (zero-deps in-memory pub/sub)

**Config:** `titan/config.py` — pydantic-settings loading from `.env`. All secrets in `.env` only.

**Database:** SQLAlchemy async with `async_session_factory`. SQLite dev, MongoDB Atlas prod. 37 ORM models with UUID PKs in `Database/models/`.

## Structure

```
MCP/                    FastMCP server + 26 tool modules + Pydantic schemas
Services/agents/        24 agent implementations (product, review, ugc, creative, etc.)
Services/orchestrator.py  CEO Agent — imports and coordinates all agents
Services/graph_workflow.py  LangGraph state graph (DISCOVER→ANALYZE→CREATE→PUBLISH)
Services/notion/        Notion API client + dashboard sync (3 databases)
Services/mongodb/       MongoDB Atlas client + Atlas Admin API
Services/gdrive/        Google Drive 5TB + model store
Services/memory/        ChromaDB vector store for hooks/products
Services/publisher/     BrowserUse auto-upload to 6 platforms + anti-shadowban
Workers/                Kaggle T4 notebooks (FLUX image, Wan 2.2 video, LoRA)
Database/               SQLAlchemy async connection + 37 ORM models + repository
titan/                  FastAPI app, autonomous loop, launch controller, config
Tests/                  12 test files, 67 tests
AGENTS/                 17 agent specification docs
```

## Development Rules

- Typed Python: every function annotated with return types
- Async first: no blocking I/O in agent/tool code
- Kaggle workers = generation only, no business logic, no API keys
- GPU constraint: T4 Tesla only (never P100/A100)
- Secrets in `.env` (gitignored), never in code
- DI pattern: agents get sessions via `AgentContext`, singletons only for `config.settings`
- MCP tool files are thin: validate input → call core function → return output
