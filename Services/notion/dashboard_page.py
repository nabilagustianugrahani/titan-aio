"""Notion Dashboard Page — auto-update TITAN AIO summary page."""

from __future__ import annotations

from Services.notion.client import NotionClient
from Services.notion.sync import NotionDashboard
from titan.config import settings


class NotionPageUpdater:
    """Update the TITAN AIO parent page with live summary stats."""

    PARENT_PAGE_ID = "37f5784a-c9f8-815e-a718-d2f5986d12fb"

    def update_summary(self) -> dict:
        """Append/update summary blocks on the TITAN AIO page."""
        nc = NotionClient.get_instance()
        client = nc.client
        db = NotionDashboard()

        # Get data from Notion DBs
        campaigns = db.list_active_campaigns(limit=50)
        tasks = db.list_pending_tasks(limit=50)
        knowledge = db.query_knowledge(limit=50)

        # Aggregate
        total_revenue = sum(c.get("revenue", 0) or 0 for c in campaigns)
        total_commission = total_revenue * 0.05  # estimated
        categories: dict[str, int] = {}
        for k in knowledge:
            cat = k.get("category") or "Uncategorized"
            categories[cat] = categories.get(cat, 0) + 1

        # Build summary text
        cat_summary = " | ".join(f"{cat}: {count}" for cat, count in categories.items())
        summary = (
            f"📊 **TITAN AIO — Live Summary**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 Total Revenue: Rp {total_revenue:,.0f}\n"
            f"💸 Est. Commission: Rp {total_commission:,.0f}\n"
            f"📊 Active Campaigns: {len(campaigns)}\n"
            f"📋 Pending Tasks: {len(tasks)}\n"
            f"🧠 Knowledge: {len(knowledge)} entries\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        )

        # Get existing blocks and find/update summary block
        blocks = client.blocks.children.list(block_id=self.PARENT_PAGE_ID)
        existing_summary_id = None

        for block in blocks.get("results", []):
            if block.get("type") == "callout":
                rich_text = block.get("callout", {}).get("rich_text", [])
                for t in rich_text:
                    if "TITAN AIO — Live Summary" in t.get("plain_text", ""):
                        existing_summary_id = block["id"]
                        break
                if existing_summary_id:
                    break

        # Build rich text for summary
        rich_text = []
        for line in summary.split("\n"):
            bold = line.startswith("📊") or line.startswith("━━")
            rich_text.append({
                "type": "text",
                "text": {"content": line + "\n" if not line.startswith("━━") else line + "\n"},
                "annotations": {"bold": bold, "color": "default"},
            })

        callout_props = {
            "rich_text": rich_text,
            "icon": {"type": "emoji", "emoji": "📊"},
            "color": "blue_background",
        }

        try:
            if existing_summary_id:
                client.blocks.update(block_id=existing_summary_id, **callout_props)
                return {"action": "updated", "block_id": existing_summary_id}
            else:
                new_block = client.blocks.children.append(
                    block_id=self.PARENT_PAGE_ID,
                    children=[{"object": "block", "type": "callout", "callout": callout_props, "position": 1}],
                )
                return {"action": "created", "block_id": new_block.get("results", [{}])[0].get("id", "")}
        except Exception as e:
            return {"error": str(e)}
