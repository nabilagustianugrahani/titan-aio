# TITAN AIO — Agent Specifications

## Architecture

```
CEO Agent (orchestrator — never generates content)
  ├── Core Agents (Phase 1)
  │   ├── Product Agent     → Product Score
  │   ├── Review Agent      → Review Intelligence
  │   ├── UGC Agent         → Hooks + Scripts
  │   ├── Creative Agent    → Thumbnails + Storyboards
  │   └── Offer Agent       → Offer Strategy
  ├── Intelligence Agents (Phase 2)
  │   ├── Trend Agent       → Trend Score
  │   ├── Competitor Agent  → Swipe Intelligence
  │   ├── Memory Agent      → Knowledge Storage
  │   └── Analytics Agent   → Campaign Metrics
  ├── Media Agents (Phase 3)
  │   ├── Video Agent       → Video Assets
  │   └── Avatar Agent      → Avatar Assets
  └── Scale Agents (Phase 4)
      ├── Publisher Agent   → Publishing Package
      ├── Finance Agent     → Profit Intelligence
      └── Growth Agent      → Growth Strategy
```

## Agent I/O Contracts

Every agent has:
- **Input**: Pydantic model or kwargs
- **Output**: Pydantic model or typed dict
- **Dependencies**: Listed explicitly

### 1. CEO Agent
- **Role**: Strategic orchestrator
- **Input**: URL, user intent
- **Output**: AffiliatePackageOutput
- **Never**: Generates content
- **Location**: `Services/orchestrator.py`

### 2. Product Agent
- **Input**: URL → **Output**: AnalyzeProductOutput
- **Fields**: price, sales, rating, commission, competition, score

### 3. Review Agent
- **Input**: product_id → **Output**: AnalyzeReviewsOutput
- **Fields**: pain_points, objections, benefits, complaints, sentiment

### 4. UGC Agent
- **Input**: product_id, offer_strategy → **Output**: hooks[], scripts[]
- **Target**: 10 hooks + 10 scripts minimum

### 5. Creative Agent
- **Input**: product_id → **Output**: thumbnail_concepts, storyboards
- **Variations**: bold, comparison, lifestyle, minimal

### 6. Offer Agent
- **Input**: product + reviews + competitors → **Output**: offer strategy
- **Fields**: angle, positioning, value prop, CTA

### 7. Trend Agent
- **Input**: category → **Output**: trend_score, velocity, direction

### 8. Competitor Agent
- **Input**: category → **Output**: winning_hooks, gaps, differentiation

### 9. Memory Agent
- **Input**: action (store/find) + data → **Output**: stored/retrieved knowledge

### 10. Analytics Agent
- **Input**: campaign_id → **Output**: views, CTR, conversions, revenue

### 11. Video Agent
- **Input**: script + model → **Output**: video URL

### 12. Avatar Agent
- **Input**: persona name → **Output**: avatar_id, image_url, persona

### 13. Publisher Agent
- **Input**: caption + assets → **Output**: platform-formatted posts

### 14. Finance Agent
- **Input**: campaign_id + revenue + spend → **Output**: profit + ROI

### 15. Growth Agent
- **Input**: ROI → **Output**: scale/kill/maintain decision

### 16. Knowledge Agent
- **Input**: (implicit from Memory) → **Output**: playbooks, patterns
