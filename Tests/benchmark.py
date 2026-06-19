"""Performance benchmark for Titan AIO pipeline.

Measures end-to-end timing for:
1. Individual agent execution
2. Full CEO pipeline (synchronous)
3. LangGraph workflow
4. MCP tool calls

Run: python -m Tests.benchmark
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path

# Set test DB
_TEST_DB = str(Path(__file__).resolve().parent.parent / "test.db")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:////{_TEST_DB.removeprefix('/')}"


async def bench(label: str, fn, **kwargs) -> dict:
    """Run a benchmark function and return timing."""
    t0 = time.perf_counter()
    try:
        result = await fn(**kwargs)
        elapsed = time.perf_counter() - t0
        return {"label": label, "time_ms": round(elapsed * 1000, 1), "status": "ok", "result_size": _size(result)}
    except Exception as e:
        elapsed = time.perf_counter() - t0
        return {"label": label, "time_ms": round(elapsed * 1000, 1), "status": "error", "error": str(e)[:100]}


def _size(obj) -> int:
    """Rough size estimate."""
    if isinstance(obj, dict):
        return len(obj)
    if isinstance(obj, list):
        return len(obj)
    return 1


async def run_benchmarks():
    print("=" * 60)
    print("TITAN AIO — Performance Benchmark")
    print("=" * 60)

    results = []

    # ── Individual agents ──
    print("\n📦 Individual Agents:")

    from Services.agents.trend import TrendAgent
    r = await bench("TrendAgent", lambda: TrendAgent()(category="elektronik"))
    results.append(r)

    from Services.agents.competitor import CompetitorAgent
    r = await bench("CompetitorAgent", lambda: CompetitorAgent()(category="elektronik"))
    results.append(r)

    from Services.agents.analytics import AnalyticsAgent
    r = await bench("AnalyticsAgent", lambda: AnalyticsAgent()(campaign_id="test"))
    results.append(r)

    from Services.agents.knowledge import KnowledgeAgent
    r = await bench("KnowledgeAgent", lambda: KnowledgeAgent()())
    results.append(r)

    from Services.agents.publisher import PublisherAgent
    r = await bench("PublisherAgent", lambda: PublisherAgent()(caption="Test product review"))
    results.append(r)

    from Services.agents.video import VideoAgent
    r = await bench("VideoAgent", lambda: VideoAgent()(script="Review power bank terbaik 2024"))
    results.append(r)

    from Services.agents.content import ContentAgent
    r = await bench("ContentAgent", lambda: ContentAgent()(product_id="test", category="elektronik"))
    results.append(r)

    from Services.agents.product import ProductAgent
    r = await bench("ProductAgent", lambda: ProductAgent()(url="https://shopee.co.id/product/1"))
    results.append(r)

    from Services.agents.review import ReviewAgent
    r = await bench("ReviewAgent", lambda: ReviewAgent()(product_id="test-prod-0"))
    results.append(r)

    # ── Full CEO pipeline ──
    print("\n🏗️ Full CEO Pipeline:")
    from Services.orchestrator import CEOAgent
    ceo = CEOAgent()

    r = await bench("CEO Full Pipeline", lambda: ceo.create_affiliate_package(url="https://shopee.co.id/product/1"))
    results.append(r)

    # ── Results ──
    print("\n" + "=" * 60)
    print(f"{'Label':<25} {'Time (ms)':>10} {'Status':>8} {'Size':>6}")
    print("-" * 60)
    total = 0
    for r in results:
        status = "✅" if r["status"] == "ok" else "❌"
        print(f"{r['label']:<25} {r['time_ms']:>8.1f}ms {status:>8} {r.get('result_size', 0):>6}")
        total += r["time_ms"]

    print("-" * 60)
    print(f"{'TOTAL':<25} {total:>8.1f}ms")
    print(f"{'AVERAGE':<25} {total/len(results):>8.1f}ms")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_benchmarks())
