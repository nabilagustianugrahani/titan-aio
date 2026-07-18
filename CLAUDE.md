# TITAN AIO — Claude Code Guide

## Sekilas

Autonomous affiliate intelligence OS. Input: URL Shopee/Tokopedia → output: campaign lengkap (analisis, hooks, script, gambar, video, caption) + Notion + GDrive.

## Commands

```bash
uv run python -m titan.main           # server → :8080/dashboard
uv run pytest Tests/ -v               # test
uv run ruff check .                   # lint
uv run python MCP/standalone.py       # MCP stdio
./run.sh launch <url>                 # campaign one-shot
./run.sh loop                         # mode kontinu
```

## Arsitektur

```
URL → MCP Server (FastMCP, 48 tools) → CEO Agent → pipeline agents → Notion + GDrive
```

**3 orchestration paths:**
1. CEO Agent (`Services/orchestrator.py`) — sequential via MessageBus
2. LangGraph (`Services/graph_workflow.py`) — state graph + parallel
3. Autonomous Pipeline (`Services/autonomous_pipeline.py`) — end-to-end

## Agent Pattern

Semua agent di `Services/agents/`, extend `BaseAgent`, komunikasi via `MessageBus` pub/sub. Agent terima `AgentContext(session=AsyncSession)`, jangan bikin session sendiri.

## Database

SQLAlchemy async + `Repository[ModelT]` generic CRUD. SQLite dev, MongoDB prod. UUID PK.

## ⚠️ GPU Work → Remote

GPU berat (torch, diffusers, opencv) jalan di remote workers — DashScope, Google Veo, Kaggle, Modal. Server ini (HF Space) cuma buat orchestration code ringan.

## Video Pipeline Priority

1. DashScope Wan 2.7 I2V (cloud API)
2. Google Veo 2 (cloud API)
3. Kaggle T4 x2 (free GPU)
4. Modal A100 (paid)

## Struktur

| Folder | Isi |
|--------|-----|
| `MCP/tools/` | 48 tool wrappers (Pydantic in/out) |
| `Services/agents/` | 20+ agent + BaseAgent + MessageBus |
| `Database/` | SQLAlchemy async + models + repository |
| `titan/` | FastAPI app + config + launch controller |
| `Services/` | orchestrator, pipeline, notion, gdrive, publisher, dll |
| `Workers/` | Kaggle/Modal GPU workers |
| `Tests/` | 12 files, 66 tests |
