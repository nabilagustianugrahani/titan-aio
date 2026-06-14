# TITAN AIO — Autonomous Affiliate Intelligence Operating System

**Version:** 1.0
**Mode:** AUTONOMOUS BUILD

---

## MISSION

Titan does not exist to generate images.
Titan does not exist to generate videos.
Titan **exists to generate profitable affiliate campaigns.**

**MAXIMIZE AFFILIATE REVENUE** while minimizing human effort.

---

## OPERATING SYSTEM

Read **every file** inside `.titan/`:

```
.titan/
├── CLAUDE.md              ← this file (project constitution)
├── AUTONOMOUS_MODE.md     ← autonomous execution protocol — READ FIRST
├── PROJECT_STATUS.md      ← live status, next task
├── ROADMAP.md             ← phased deliverables
├── ARCHITECTURE.md        ← system architecture
├── DEVELOPMENT_RULES.md   ← coding standards, forbidden patterns
├── AGENT_SPECS.md         ← all 16 agent specifications
├── MCP_SPECS.md           ← all 22 MCP tool specifications
├── DATABASE_SPECS.md      ← schema, tables, repository pattern
├── WORKER_SPECS.md        ← Kaggle worker specs
├── TESTING_RULES.md       ← test coverage requirements
└── DEPLOYMENT_PLAN.md     ← deployment stages
```

---

## CORE PHILOSOPHY

Every feature must improve one of:
1. **More Clicks**
2. **More Conversions**
3. **More Revenue**
4. **Better Automation**

If a feature doesn't improve one of these, it's lower priority.

---

## PRODUCT VISION

**Input:** Shopee/Tokopedia/affiliate product URL
**Output:** Complete Affiliate Package:
- Product Intelligence
- Review Intelligence
- Competitor Intelligence
- 10 Winning Hooks
- 10 UGC Scripts
- Thumbnails
- Images
- Videos
- Captions + CTA
- Posting Recommendations

**Without manual content creation.**

---

## TECH STACK

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI, FastMCP |
| Agent Framework | CrewAI |
| Workflow Engine | LangGraph |
| Database | PostgreSQL (asyncpg) / SQLite (dev) |
| Vector Memory | ChromaDB |
| Queue | Redis |
| Storage | S3-compatible |
| Image Gen | FLUX Schnell/Dev (Kaggle T4) |
| Video Gen | Wan 2.2 / Hunyuan Video (Kaggle T4) |
| Training | Kohya / SimpleTuner (Kaggle T4) |

---

## SUCCESS METRICS

1. CTR
2. Conversion Rate
3. Revenue
4. Commission
5. ROI

> These matter more than video count, image count, or agent count.

---

**See `.titan/` for full specifications. Operate in autonomous mode per `.titan/AUTONOMOUS_MODE.md`.**
