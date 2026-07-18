# Titan AIO — Production Ready Design

> **Date:** 2026-06-22
> **Scope:** 3 subsystems — Dashboard, Revenue Pipeline, Telegram Alerts

---

## Overview

Upgrade Titan AIO from "built" to "production-ready" with:
1. **Real-time Dashboard** — WebSocket-powered monitoring of all 50+ features
2. **Revenue Pipeline** — Auto-publish + affiliate commission tracking + ROI
3. **Telegram Alerts** — Critical notifications to Telegram bot

---

## 1. Real-Time Dashboard

### Architecture
```
Browser ← WebSocket ← FastAPI ← Pipeline/Agents
   │                        │
   └── REST API ←───────────┘
```

### Components

#### A. WebSocket Server (`titan/websocket_server.py`)
- Already exists (ConnectionManager)
- Add: pipeline status broadcasting, metric streaming
- Add: client subscription system (subscribe to specific events)

#### B. Dashboard Routes (`titan/main.py`)
New endpoints:
- `GET /dashboard` — main dashboard page
- `GET /api/dashboard/stats` — revenue, campaigns, knowledge stats
- `GET /api/dashboard/chart` — 7-day revenue time series
- `GET /api/dashboard/campaigns` — active campaigns list
- `GET /api/dashboard/pipeline` — pipeline status
- `GET /api/dashboard/alerts` — recent alerts
- `GET /api/dashboard/trends` — trending topics
- `GET /api/dashboard/competitors` — competitor watch list
- `POST /api/dashboard/refresh` — force refresh cached data

#### C. Dashboard UI (`titan/templates/dashboard.html`)
Sections:
1. **Header** — system status, uptime, connection status
2. **Revenue Card** — total revenue, ROI, trend (Chart.js)
3. **Pipeline Status** — current/last pipeline run, phase, progress bar
4. **Campaigns Table** — active campaigns with metrics
5. **Trending Topics** — live trending from TikTok/Shopee
6. **Alerts Panel** — critical alerts, sentiment warnings
7. **Competitor Watch** — monitored competitors with metrics
8. **Quick Actions** — launch campaign, view report, manage calendar

#### D. CSS (`titan/static/dashboard.css`)
- Dark mode (default)
- Responsive grid layout
- Real-time indicator (green dot = connected)
- Chart.js for revenue graph
- WebSocket status indicator

### Data Flow
1. Pipeline runs → publishes events to MessageBus
2. MessageBus → WebSocket broadcasts to connected clients
3. Browser receives update → DOM updates in real-time
4. REST endpoints for historical data (charts, tables)

---

## 2. Revenue Pipeline

### Architecture
```
Product URL → Shopee/Tokopedia API → Content Generation → 
  → Auto-Publish (TikTok/IG/FB) → Track Clicks → 
  → Track Conversions → Calculate Revenue → Update Dashboard
```

### Components

#### A. Affiliate Tracker (`Services/revenue/tracker.py`)
- Track clicks per affiliate link
- Track conversions per platform
- Calculate commission per sale
- Daily/weekly/monthly revenue aggregation
- ROI calculation (revenue - ad_spend)

#### B. Auto-Publisher (`Services/publisher/auto_publish.py`)
- Already exists (BrowserUse-based)
- Upgrade: integrate with Content Calendar
- Upgrade: compliance check before publishing
- Upgrade: A/B variant publishing

#### C. Revenue API (`MCP/tools/revenue_tools.py`)
- `record_affiliate_click(link_id, platform, source)`
- `record_conversion(link_id, amount, commission)`
- `get_revenue_report(period, platform)`
- `get_roi_analysis(campaign_id)`
- `get_top_performing_products()`

#### D. Revenue Dashboard Widget
- 7-day revenue chart (Chart.js)
- Top performing products table
- Commission breakdown by platform
- ROI trend line

### Data Flow
1. Content published → affiliate link generated
2. User clicks link → tracked via redirect
3. User converts → commission recorded
4. Revenue aggregated → dashboard updated
5. Telegram alert on significant events

---

## 3. Telegram Alerts

### Architecture
```
Event → Alert Manager → Telegram Bot → User's Phone
```

### Components

#### A. Alert Rules (`Services/notifications/alert_rules.py`)
Pre-configured rules:
- Pipeline complete → ✅ alert
- Pipeline failed → 🚨 critical alert
- Revenue milestone ($10, $50, $100) → 🎉 celebration
- Competitor detected → 👁️ watch alert
- Sentiment crisis → 🚨 crisis alert
- Daily summary → 📊 report

#### B. Telegram Integration
- Already exists (TelegramBot)
- Upgrade: connect to MessageBus events
- Upgrade: format alerts with inline keyboards
- Add: /status command (quick pipeline status)
- Add: /revenue command (today's earnings)

#### C. Alert Formatting
```python
# Pipeline Complete
✅ Pipeline Complete
Product: {product_name}
Score: {viral_score}/100
Revenue Forecast: ${forecast}

# Daily Summary
📊 Daily Report
Campaigns: {count}
Revenue: ${total}
Top Product: {product}
Alerts: {alert_count}
```

### Data Flow
1. Event occurs → AlertManager checks rules
2. Rule matched → format alert message
3. Send to Telegram → user receives notification
4. Log to audit trail

---

## Implementation Order

1. **Phase 1: Dashboard** (1-2 hours)
   - Update dashboard.html with WebSocket integration
   - Add new API endpoints
   - Update CSS for new sections

2. **Phase 2: Revenue Pipeline** (1-2 hours)
   - Create affiliate tracker
   - Wire to existing auto-publisher
   - Add revenue dashboard widget

3. **Phase 3: Telegram Alerts** (30 min)
   - Connect to MessageBus
   - Configure alert rules
   - Test notifications

4. **Phase 4: Integration** (30 min)
   - Wire all three together
   - End-to-end testing
   - Deploy to VPS

---

## Testing

- Dashboard: visual verification (WebSocket connection, real-time updates)
- Revenue: mock affiliate clicks, verify tracking
- Telegram: send test alerts, verify delivery
- Integration: full pipeline run → dashboard update → Telegram alert

---

## Dependencies

- Existing: WebSocket server, Telegram bot, MessageBus
- New: Chart.js (CDN), SQLite for revenue tracking
- No new Python packages needed
