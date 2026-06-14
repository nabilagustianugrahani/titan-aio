# TITAN AIO — MCP Tool Specifications

## Server: `FastMCP("TITAN AIO")`
Port: 8080 (configurable)

## Tool Inventory

### Core (3)
| Tool | Input | Output | Description |
|------|-------|--------|-------------|
| `health_check` | — | `{status, version}` | System health |
| `search_products` | `query, platform, limit` | `{results[], total}` | Search products |
| `analyze_product_url` | `url` | `{product, price, rating, ...}` | Analyze product URL |

### Analysis (3)
| Tool | Input | Output | Description |
|------|-------|--------|-------------|
| `analyze_product_reviews` | `product_id, max_reviews` | `{pain_points, objections, ...}` | Review mining |
| `analyze_competitors_for_category` | `category, limit` | `{winning_hooks, gaps, ...}` | Competitor analysis |
| `generate_offer_strategy` | `product_id, analyses` | `{angle, positioning, cta}` | Offer generation |

### Content Generation (6)
| Tool | Input | Output | Description |
|------|-------|--------|-------------|
| `generate_hooks_for_product` | `product_id, offer, count` | `hooks[]` | Attention hooks |
| `generate_ugc_scripts` | `product_id, hooks, offer` | `scripts[]` | Full scripts |
| `generate_thumbnail_concept` | `product_id, style` | `{concept, description}` | Thumbnail ideas |
| `generate_product_image` | `prompt, model` | `{image_url}` | FLUX image gen |
| `generate_video_from_script` | `script, model` | `{video_url}` | Wan 2.2 video |
| `generate_ai_avatar` | `persona_name, style` | `{avatar_id, image_url}` | AI spokesperson |

### Pipeline (1)
| Tool | Input | Output | Description |
|------|-------|--------|-------------|
| `create_full_affiliate_package` | `url, include_video, include_avatar` | Full package | One-shot pipeline |

### Campaign (3)
| Tool | Input | Output | Description |
|------|-------|--------|-------------|
| `save_campaign_data` | `product_id, name, platform, budget` | `{campaign_id}` | Save campaign |
| `load_campaign_data` | `campaign_id` | Campaign details | Load campaign |
| `get_campaign_metrics` | `campaign_id` | `{views, ctr, revenue, roi}` | Campaign metrics |

### Intelligence (1)
| Tool | Input | Output | Description |
|------|-------|--------|-------------|
| `get_campaign_recommendations` | `category, limit` | `recommendations[]` | Historical recs |

### Notion (4)
| Tool | Input | Output | Description |
|------|-------|--------|-------------|
| `notion_save_campaign_data` | `campaign_id, name, ...` | `{page_id, url}` | Campaign to Notion |
| `notion_save_knowledge_entry` | `category, pattern, ...` | `{page_id, url}` | Knowledge to Notion |
| `notion_create_task_item` | `title, status, priority` | `{page_id, url}` | Task to Notion |
| `notion_list_campaigns` | `status_filter, limit` | `pages[]` | Query campaigns |

**Total: 22 tools**

## Registration Pattern
Every tool:
1. Has Pydantic input schema (validation at edge)
2. Delegates to internal service/agent
3. Returns dict (serialized Pydantic output)
4. Has docstring for LLM understanding
