import os, sys
sys.path.insert(0, "/home/Oh/projek/ugc")
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

from Services.notion.client import NotionClient
from titan.config import settings

token = settings.NOTION_TOKEN
print(f"Token: {token[:10]}...{token[-5:]}")

nc = NotionClient.get_instance()
client = nc.client

try:
    me = client.users.me()
    print(f"Connected as: {me.get('name', 'N/A')} ({me.get('id', 'N/A')[:8]}...)")

    # Search for Titan AIO
    results = client.search(query="Titan AIO").get("results", [])
    print(f"\nFound {len(results)} results:")
    for r in results:
        obj = r.get("object", "?")
        title_raw = "N/A"
        if r.get("properties"):
            for prop in r["properties"].values():
                if prop.get("type") == "title":
                    titles = prop.get("title", [])
                    if titles:
                        title_raw = titles[0].get("plain_text", "N/A")
                        break
        elif isinstance(r.get("title"), list):
            title_raw = r["title"][0].get("plain_text", "N/A") if r["title"] else "N/A"
        print(f"  [{obj}] {title_raw}")
except Exception as e:
    print(f"Error: {e}")
