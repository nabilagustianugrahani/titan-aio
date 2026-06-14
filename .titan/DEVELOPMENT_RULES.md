# TITAN AIO — Development Rules

## Mandatory Tech Stack
- **Language**: Python 3.11+
- **API**: FastAPI + FastMCP
- **Agent Framework**: CrewAI
- **Orchestration**: LangGraph
- **Database**: PostgreSQL (asyncpg)
- **Vector Store**: ChromaDB
- **Queue**: Redis
- **Storage**: S3-compatible
- **Image Gen**: FLUX Schnell/Dev (via Kaggle T4)
- **Video Gen**: Wan 2.2 / Hunyuan Video (via Kaggle T4)
- **LoRA Training**: Kohya / SimpleTuner (via Kaggle T4)

## Coding Standards

### Required
- **Fully typed** — every function has type annotations
- **Async first** — all I/O is async, no blocking calls
- **Test coverage** — every module has unit + integration tests
- **Dependency injection** — no globals, no singletons (except config)
- **Modular architecture** — one concern per file
- **Docstrings** — every module, class, and public function
- **Error handling** — every external call has try/except with logging
- **Separation of concerns** — business logic never in workers, workers never in agents

### Forbidden
- ❌ God classes / monolithic files
- ❌ Hardcoded secrets (API keys, tokens, passwords)
- ❌ Tight coupling between layers
- ❌ Duplicate code (extract shared logic)
- ❌ `except: pass` (always log or re-raise)
- ❌ Business logic inside Kaggle notebooks

## Testing Rules
See `TESTING_RULES.md` for full specification.

### Minimum per module
- 1 unit test for normal path
- 1 unit test for error/edge case
- Integration test for multi-module flows

### Coverage target: >80%

## Git Rules
- Commit after every completed task
- Message format: `phase-N: task description`
- Co-author with Claude: `Co-Authored-By: Claude <noreply@anthropic.com>`
- Never commit secrets

## Architecture Rules
1. `titan/` — app config, entry point
2. `Database/` — connection, models, repository
3. `MCP/` — FastMCP server, schemas, tools
4. `Services/` — agents, orchestrator, memory
5. `Workers/` — Kaggle worker code
6. `Tests/` — test suite

Keep this structure. No layer should import from another layer's sibling.
