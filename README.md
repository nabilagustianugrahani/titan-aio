# TITAN AIO

**Autonomous Affiliate Intelligence Operating System**

> Build affiliate campaigns. Not images. Not videos. **Revenue.**
>
> 48 MCP tools · 24 agents · 67 tests · Autonomous pipeline

---

## Quick Start

```bash
pip install -e ".[dev]"
python -m pytest Tests/ -v        # 67 tests
python -m titan.main               # Dashboard → http://localhost:8080/dashboard
```

## One-Command Campaign

```bash
python titan/autonomous_loop.py --mode once
# → Discover → Score → Create → Sync Notion
```

## Architecture

```
INPUT (keyword) → Scrape Agent → Product Agent → Review Agent
→ UGC Agent → Creative Agent → Video Worker → Publisher
→ Auto-Upload (TikTok/IG/YT/Threads/X/FB)
→ Analytics → Memory → Optimization
```

## Agents (24)

| Agent | File | Function |
|-------|------|----------|
| CEO | `orchestrator.py` | Orchestrator with MessageBus |
| Product | `product.py` | 3-score analysis |
| Review | `review.py` | Pain points, benefits |
| UGC | `ugc.py` | 10 hooks + 10 scripts |
| Creative | `creative.py` | Storyboard, thumbnails |
| Offer | `offer.py` | Positioning, CTA |
| Scrape | `scraper.py` | Auto product search |
| Commission Hunter | `commission_hunter.py` | Find highest commission |
| Anti-Shadowban | `antishadowban.py` | Platform safety |
| Affiliate | `affiliate.py` | Link generation |
| Publisher | `publisher.py` | Caption, hashtags |
| AutoUpload | `auto_upload.py` | BrowserUse upload |
| Campaign Builder | `campaign_builder.py` | Package assembly |
| Asset | `asset.py` | Download images |
| +11 more... | | |

## MCP Server (48 tools)

```bash
claude mcp add titan-aio -- python MCP/standalone.py
```

## Dashboard

```bash
python -m titan.main
# → http://localhost:8080/dashboard
```

- Revenue chart, stats cards, campaign table
- Knowledge distribution, pending tasks
- One-click "Run Campaign" button
- Auto-refresh every 30s

## Integrations

| Service | Status | Detail |
|---------|--------|--------|
| Notion | ✅ Live | Campaigns, Knowledge, Tasks DBs |
| Google Drive | ✅ Live | 5TB, asset storage + model cache |
| MongoDB Atlas | ✅ Connected | `titan_aio` cluster |
| Kaggle | ✅ Deployed | FLUX, Wan 2.2, LoRA workers (T4) |
| BrowserUse | ✅ Ready | Auto-upload 6 platforms |
| Scrapling | ✅ Installed | Product scraping |
| Playwright | ✅ Ready | Browser automation |

## Stack

```
Python 3.11+ · FastAPI · FastMCP · Playwright · ChromaDB
SQLite (dev) · MongoDB (prod) · Notion API · Google Drive API
```

## Structure

```
TITAN-AIO/
├── CLAUDE.md              ← Project constitution
├── .titan/                ← Autonomous OS (12 specs)
├── titan/                 ← FastAPI server + templates
├── MCP/                   ← 48 tools + standalone server
├── Services/              ← 23 agents + orchestrator
│   ├── agents/            ← All agent implementations
│   ├── notion/            ← Notion API + dashboard
│   ├── gdrive/            ← Google Drive storage
│   ├── mongodb/           ← Atlas client
│   └── memory/            ← ChromaDB vector store
├── Workers/               ← Kaggle notebooks
├── Database/              ← ORM + repository
├── Tests/                 ← 67 tests
└── AGENTS/                ← Agent documentation
```

## Scheduler

```bash
# Run continuously:
python -m Services.scheduler --interval 60

# Or via cron (1 cycle):
python titan/autonomous_loop.py --mode once
```

---

*Built with Claude Code · github.com/nabilagustianugrahani/titan-aio*
