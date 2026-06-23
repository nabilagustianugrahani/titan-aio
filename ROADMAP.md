# TITAN AIO — ROADMAP

## Phase 1 — MVP (Current)
**Goal:** Functioning affiliate intelligence pipeline from URL to package.

### Deliverables
- [ ] FastMCP server with health endpoint
- [ ] Product Agent — scrape & analyze product URL
- [ ] Review Agent — extract pain points, objections, benefits
- [ ] UGC Agent — generate 10 hooks + 10 scripts
- [ ] Creative Agent — thumbnail concept + storyboard
- [ ] Image Generation — FLUX pipeline via worker
- [ ] CLI/API input: product URL → affiliate package output

### Acceptance Criteria
```
Input:  https://shopee.co.id/... or https://tokopedia.com/...
Output: Product Analysis + Review Summary + 10 Hooks + 10 Scripts + Thumbnail + Image
```

### Duration Estimate
6–8 weeks

---

## Phase 2 — Intelligence
**Goal:** Add competitive awareness and persistent memory.

### Deliverables
- [ ] Trend Agent — detect trending products & market shifts
- [ ] Competitor Agent — analyze competitor ads & hooks
- [ ] Memory Agent — persist winning/failed campaign data
- [ ] Analytics Agent — track CTR, conversions, revenue
- [ ] ChromaDB integration for vector memory
- [ ] PostgreSQL schema migration for campaigns & metrics

### Duration Estimate
4–6 weeks

---

## Phase 3 — Video & Avatars
**Goal:** Full multimedia generation pipeline.

### Deliverables
- [ ] Video Agent — short-form video generation (Wan 2.7 I2V / Hunyuan)
- [ ] Avatar Agent — AI spokesperson with consistent character
- [ ] Product LoRA training pipeline (Kohya/SimpleTuner)
- [ ] LoRA policy enforcement (train only if usage_count > 20)
- [ ] Video worker setup

### Duration Estimate
6–8 weeks

---

## Phase 4 — Scale & Automate
**Goal:** Autonomous campaign lifecycle management.

### Deliverables
- [ ] Publisher Agent — auto-format & schedule to platforms
- [ ] Finance Agent — revenue, commission, ROI tracking
- [ ] Growth Agent — auto-scale winners, kill losers
- [ ] Full agent orchestration via CEO Agent
- [ ] Dashboard for campaign performance

### Duration Estimate
4–6 weeks

---

## Future Considerations

- Multi-platform support (TikTok Shop, Lazada, Amazon)
- A/B testing pipeline for creatives
- Real-time bidding integration
- API marketplace for affiliate packages
- Mobile app for campaign monitoring

---

## Guiding Principles

1. **Revenue first** — every phase must unblock revenue generation.
2. **No premature optimization** — build what's needed now.
3. **Iterate fast** — ship MVP, then layer intelligence.
4. **Workers are infra** — never put business logic in workers.
5. **Data is equity** — every campaign enriches the knowledge base.
