"""Setup Notion databases for TITAN AIO — campaigns, knowledge, tasks."""

from __future__ import annotations

from Services.notion.client import NotionClient


def setup_campaigns_db(parent_page_id: str) -> dict:
    """Create Campaigns database with proper schema."""
    nc = NotionClient.get_instance()
    client = nc.client

    db = client.databases.create(
        parent={"page_id": parent_page_id},
        title=[{"type": "text", "text": {"content": "📈 Campaigns"}}],
        properties={
            "Name": {"title": {}},
            "Campaign ID": {"rich_text": {}},
            "Product": {"rich_text": {}},
            "URL": {"url": {}},
            "Revenue": {"number": {"format": "RpIDR"}},
            "Status": {
                "select": {
                    "options": [
                        {"name": "Active", "color": "green"},
                        {"name": "Paused", "color": "yellow"},
                        {"name": "Completed", "color": "blue"},
                        {"name": "Failed", "color": "red"},
                    ]
                }
            },
            "Platform": {
                "select": {
                    "options": [
                        {"name": "Shopee", "color": "orange"},
                        {"name": "Tokopedia", "color": "green"},
                        {"name": "TikTok", "color": "pink"},
                        {"name": "Instagram", "color": "purple"},
                        {"name": "Facebook", "color": "blue"},
                    ]
                }
            },
            "Created": {"date": {}},
        },
    )
    db_id = db["id"]
    print(f"  ✅ Campaigns DB: {db_id}")
    print(f"     → Add to .env: NOTION_CAMPAIGN_DB={db_id}")
    return {"database_id": db_id, "url": db.get("url", "")}


def setup_knowledge_db(parent_page_id: str) -> dict:
    """Create Knowledge database with proper schema."""
    nc = NotionClient.get_instance()
    client = nc.client

    db = client.databases.create(
        parent={"page_id": parent_page_id},
        title=[{"type": "text", "text": {"content": "🧠 Knowledge Base"}}],
        properties={
            "Name": {"title": {}},
            "Category": {
                "select": {
                    "options": [
                        {"name": "Products", "color": "blue"},
                        {"name": "Hooks", "color": "purple"},
                        {"name": "Scripts", "color": "green"},
                        {"name": "Pain Points", "color": "red"},
                        {"name": "Competitors", "color": "orange"},
                    ]
                }
            },
            "Pattern": {"rich_text": {}},
            "Confidence": {"number": {"format": "percent"}},
            "Advice": {"rich_text": {}},
            "Source Campaign": {"rich_text": {}},
            "Tags": {"multi_select": {"options": []}},
        },
    )
    db_id = db["id"]
    print(f"  ✅ Knowledge DB: {db_id}")
    print(f"     → Add to .env: NOTION_KNOWLEDGE_DB={db_id}")
    return {"database_id": db_id, "url": db.get("url", "")}


def setup_tasks_db(parent_page_id: str) -> dict:
    """Create Tasks database with proper schema."""
    nc = NotionClient.get_instance()
    client = nc.client

    db = client.databases.create(
        parent={"page_id": parent_page_id},
        title=[{"type": "text", "text": {"content": "📋 Tasks"}}],
        properties={
            "Name": {"title": {}},
            "Status": {
                "select": {
                    "options": [
                        {"name": "Pending", "color": "yellow"},
                        {"name": "In Progress", "color": "blue"},
                        {"name": "Done", "color": "green"},
                        {"name": "Blocked", "color": "red"},
                    ]
                }
            },
            "Priority": {
                "select": {
                    "options": [
                        {"name": "High", "color": "red"},
                        {"name": "Medium", "color": "yellow"},
                        {"name": "Low", "color": "gray"},
                    ]
                }
            },
        },
    )
    db_id = db["id"]
    print(f"  ✅ Tasks DB: {db_id}")
    print(f"     → Add to .env: NOTION_TASKS_DB={db_id}")
    return {"database_id": db_id, "url": db.get("url", "")}


def main() -> None:
    """CLI: python -m Services.notion.setup_dbs <parent_page_id>"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m Services.notion.setup_dbs <parent_page_id>")
        print()
        print("Cara pakai:")
        print("1. Buka Notion → buat page baru (contoh: 'Titan AIO')")
        print("2. Copy page ID dari URL (bagian setelah last slash)")
        print("3. Jalankan: python -m Services.notion.setup_dbs <page_id>")
        print()
        print("Contoh URL:")
        print("  https://notion.so/My-Workspace/abc123def456...")
        print("                                   ^^^^^^^^^^^")
        print("                                   ini page ID-nya")
        return

    parent_id = sys.argv[1].replace("-", "")
    # Notion page IDs need dashes for API
    if len(parent_id) == 32:
        parent_id = f"{parent_id[:8]}-{parent_id[8:12]}-{parent_id[12:16]}-{parent_id[16:20]}-{parent_id[20:]}"

    print("🔧 Setting up TITAN AIO Notion databases...\n")

    campaigns = setup_campaigns_db(parent_id)
    knowledge = setup_knowledge_db(parent_id)
    tasks = setup_tasks_db(parent_id)

    print("\n📋 Tambahkan ke .env:")
    print(f"NOTION_CAMPAIGN_DB={campaigns['database_id']}")
    print(f"NOTION_KNOWLEDGE_DB={knowledge['database_id']}")
    print(f"NOTION_TASKS_DB={tasks['database_id']}")
    print("\n✨ Done! Buka Notion untuk lihat databases.")


if __name__ == "__main__":
    main()
