---
title: TITAN AIO
emoji: 🤖
colorFrom: indigo
colorTo: purple
sdk: docker
pinned: false
license: mit
---

# TITAN AIO

**Autonomous Affiliate Intelligence Operating System**

> Build affiliate campaigns. Not images. Not videos. **Revenue.**
>
> 48 MCP tools · 22 agents · 66 tests · Autonomous pipeline

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
# → Discover → Analyze → Create → Publish → Track
```

## Architecture

```
INPUT (keyword) → Scrape Agent → Product Agent → Review Agent
→ Content Agent (hooks + scripts + thumbnails + storyboards)
→ Video Worker → Publisher (6 platforms)
→ Analytics → Memory → Optimization
```

## Agents (20)

| Agent | File | Function |
|-------|------|----------|
| CEO | `orchestrator.py` | Orchestrator with MessageBus |
| Product | `product.py` | 3-score analysis |
| Review | `review.py` | Pain points, benefits |
| **Content** | `content.py` | **Hooks + scripts + thumbnails + storyboards** |
| Offer | `offer.py` | Positioning, CTA |
| Scrape | `scraper.py` | Auto product search |
| Trend | `trend.py` | DB + social listening |
| Competitor | `competitor.py` | Angle extraction, gap analysis |
| Analytics | `analytics.py` | CTR, ROI, per-platform metrics |
| Knowledge | `knowledge.py` | Pattern synthesis, playbooks |
| Publisher | `publisher.py` | Per-platform formatting + anti-shadowban |
| Video | `video.py` | Shot planning, worker dispatch |
| Commission Hunter | `commission_hunter.py` | Find highest commission |
| Anti-Shadowban | `antishadowban.py` | Platform safety |
| Affiliate | `affiliate.py` | Link generation |
| Campaign Builder | `campaign_builder.py` | Package assembly |
| Asset | `asset.py` | Download images |
| Avatar | `avatar.py` | AI spokesperson |
| Finance | `finance.py` | Revenue, commission tracking |
| Growth | `growth.py` | Auto-scale winners, kill losers |
| Memory | `memory.py` | ChromaDB vector store |
| Message Bus | `message_bus.py` | Inter-agent events |

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

## LangGraph Workflow

```
discover → trends → product → [reviews ‖ competitors]
→ offer → content → [optimize hooks or affiliate]
→ captions → finalize → analytics → END
```

13 nodes · parallel fan-out · conditional branching · self-healing retries

## Benchmark

```
TrendAgent        16ms   ✅
CompetitorAgent    6ms   ✅
AnalyticsAgent     2ms   ✅
KnowledgeAgent    68ms   ✅
PublisherAgent     0.3ms ✅
VideoAgent         0.1ms ✅
ContentAgent      29ms   ✅
ProductAgent      19ms   ✅
ReviewAgent       26ms   ✅
CEO Full Pipeline  68ms  ✅
```

## Integrations

| Service | Status | Detail |
|---------|--------|--------|
| Notion | ✅ Live | Campaigns, Knowledge, Tasks DBs |
| Google Drive | ✅ Live | 5TB, asset storage + model cache |
| MongoDB Atlas | ✅ Connected | `titan_aio` cluster |
| BrowserUse | ✅ Ready | Auto-upload 6 platforms |
| Scrapling | ✅ Installed | Product scraping |
| Playwright | ✅ Ready | Browser automation |

## Stack

```
Python 3.11+ · FastAPI · FastMCP · LangGraph · Playwright · ChromaDB
SQLite (dev) · MongoDB (prod) · Notion API · Google Drive API
```

## Structure

```
TITAN-AIO/
├── CLAUDE.md              ← Project constitution
├── titan/                 ← FastAPI server + templates
├── MCP/                   ← 48 tools + standalone server
├── Services/              ← 22 agents + orchestrator
│   ├── agents/            ← All agent implementations
│   ├── notion/            ← Notion API + dashboard
│   ├── gdrive/            ← Google Drive storage
│   ├── mongodb/           ← Atlas client
│   ├── memory/            ← ChromaDB vector store
│   └── publisher/         ← Auto-upload + anti-shadowban
├── Workers/               ← GPU worker dispatchers
├── Database/              ← ORM + repository (37 models)
├── Tests/                 ← 66 tests + benchmark
└── AGENTS/                ← Agent documentation
```

## CI/CD

GitHub Actions: test on Python 3.11 + 3.12 on every push.

---

*Built with Claude Code · github.com/nabilagustianugrahani/titan-aio*
