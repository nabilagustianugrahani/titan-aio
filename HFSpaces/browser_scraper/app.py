"""HF Space — BrowserUse Product Scraper

Deploy: Upload to HuggingFace Spaces (Gradio SDK)
Usage:  POST /api/search  or  /api/details
"""

import asyncio
import json
import re
from typing import Optional

import gradio as gr

# ── BrowserUse scraper ──────────────────────────────────────────

async def search_products(keyword: str, platform: str = "shopee", max_results: int = 10) -> dict:
    """Search products using BrowserUse."""
    try:
        from browser_use import Browser
        from browser_use.config import Config as BrowserConfig
    except ImportError:
        return {"error": "browser-use not installed", "products": []}

    urls = {
        "shopee": f"https://shopee.co.id/search?keyword={keyword}&sortBy=sales",
        "tokopedia": f"https://www.tokopedia.com/search?q={keyword}&st=product&ob=5",
    }
    url = urls.get(platform)
    if not url:
        return {"error": f"Unknown platform: {platform}", "products": []}

    browser = Browser(config=BrowserConfig(headless=True))
    try:
        page = await browser.get(url)
        await page.wait_for_load_state("networkidle")

        # Extract products using BrowserUse AI
        products = await page.evaluate("""() => {
            const items = [];
            const cards = document.querySelectorAll('[data-sqe="item"], [class*="product"], [class*="card"]');
            cards.forEach((card, i) => {
                if (i >= %d) return;
                const title = card.querySelector('[class*="name"], [class*="title"]')?.textContent?.trim() || '';
                const price = card.querySelector('[class*="price"]')?.textContent?.trim() || '0';
                const rating = card.querySelector('[class*="rating"]')?.textContent?.trim() || '';
                const link = card.querySelector('a[href]')?.href || '';
                if (title) items.push({title, price, rating, url: link});
            });
            return items;
        }""" % max_results)

        return {"products": products, "platform": platform, "keyword": keyword}
    except Exception as e:
        return {"error": str(e), "products": []}
    finally:
        await browser.close()


async def get_product_details(url: str) -> dict:
    """Get product details using BrowserUse."""
    try:
        from browser_use import Browser
        from browser_use.config import Config as BrowserConfig
    except ImportError:
        return {"error": "browser-use not installed"}

    browser = Browser(config=BrowserConfig(headless=True))
    try:
        page = await browser.get(url)
        await page.wait_for_load_state("networkidle")

        details = await page.evaluate("""() => {
            const title = document.querySelector('title')?.textContent?.trim() || 'Unknown';
            const priceEl = document.querySelector('[class*="price"]');
            const price = priceEl?.textContent?.trim() || '0';
            const ratingEl = document.querySelector('[class*="rating"]');
            const rating = ratingEl?.textContent?.trim() || '';
            const salesEl = document.querySelector('[class*="sales"], [class*="sold"]');
            const sales = salesEl?.textContent?.trim() || '0';
            return {title, price, rating, sales};
        }""")

        return {
            "title": details.get("title", "Unknown"),
            "price": _parse_price(details.get("price", "0")),
            "rating": _parse_rating(details.get("rating", "")),
            "sales": _parse_sales(details.get("sales", "0")),
            "url": url,
            "source": "browseruse",
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        await browser.close()


def _parse_price(text: str) -> float:
    """Parse price from text like 'Rp 150.000' or 'IDR 150000'."""
    m = re.search(r'[\d.,]+', text.replace(".", "").replace(",", "."))
    return float(m.group()) if m else 0


def _parse_rating(text: str) -> Optional[float]:
    """Parse rating from text."""
    m = re.search(r'[\d.]+', text)
    return float(m.group()) if m else None


def _parse_sales(text: str) -> int:
    """Parse sales from text like '1,2rb terjual'."""
    m = re.search(r'[\d.,]+', text)
    if not m:
        return 0
    num = float(m.group().replace(",", "."))
    if "rb" in text.lower() or "k" in text.lower():
        num *= 1000
    return int(num)


# ── Gradio UI ──────────────────────────────────────────────────

with gr.Blocks(title="TITAN Browser Scraper") as demo:
    gr.Markdown("# 🔍 TITAN Browser Scraper")
    gr.Markdown("BrowserUse-powered product scraping for Shopee/Tokopedia")

    with gr.Tab("Search"):
        keyword = gr.Textbox(label="Keyword", placeholder="power bank 20000mah")
        platform = gr.Radio(["shopee", "tokopedia"], value="shopee", label="Platform")
        max_results = gr.Slider(1, 50, value=10, label="Max Results")
        search_btn = gr.Button("Search", variant="primary")
        search_output = gr.JSON(label="Results")

        search_btn.click(
            fn=search_products,
            inputs=[keyword, platform, max_results],
            outputs=search_output,
        )

    with gr.Tab("Product Details"):
        url = gr.Textbox(label="Product URL", placeholder="https://shopee.co.id/...")
        details_btn = gr.Button("Get Details", variant="primary")
        details_output = gr.JSON(label="Details")

        details_btn.click(
            fn=get_product_details,
            inputs=[url],
            outputs=details_output,
        )

    gr.Examples(
        examples=[
            ["power bank 20000mah", "shopee", 10],
            ["tws earbuds", "tokopedia", 5],
        ],
        inputs=[keyword, platform, max_results],
    )


if __name__ == "__main__":
    demo.launch()
