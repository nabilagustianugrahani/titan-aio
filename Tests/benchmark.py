"""Performance benchmark for Titan AIO pipeline.

Measures end-to-end timing + memory for:
1. Individual agent execution (Product, Review, UGC/Content, Offer)
2. MCP tool calls (health, generate_offer, generate_hooks, generate_script)
3. Full pipeline (create_affiliate_package)

Usage:
    python Tests/benchmark.py              # run all benchmarks
    python Tests/benchmark.py --repeat 3   # repeat each N times
    python Tests/benchmark.py --json       # JSON output only
    python Tests/benchmark.py --output results.json
"""

from __future__ import annotations

import asyncio
import gc
import json
import os
import sys
import time
import tracemalloc
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Coroutine

# ── Ensure project root on sys.path ──────────────────────────────

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# ── Set test DB before any imports ────────────────────────────────

_TEST_DB = str(Path(_PROJECT_ROOT) / "test.db")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:////{_TEST_DB.removeprefix('/')}"


# ── Result model ──────────────────────────────────────────────────

@dataclass
class BenchResult:
    name: str
    category: str
    elapsed_ms: float
    mem_peak_kb: float
    success: bool = True
    error: str = ""
    iterations: int = 1
    avg_ms: float = 0.0

    def __post_init__(self) -> None:
        self.avg_ms = self.elapsed_ms / max(self.iterations, 1)


# ── Timing / memory helper ────────────────────────────────────────

async def _bench(
    name: str,
    category: str,
    fn: Callable[..., Coroutine[Any, Any, Any]],
    *args: Any,
    repeat: int = 1,
    **kwargs: Any,
) -> BenchResult:
    gc.collect()
    tracemalloc.start()
    t0 = time.perf_counter()
    error_msg = ""
    success = True
    try:
        for _ in range(repeat):
            await fn(*args, **kwargs)
    except Exception as exc:
        success = False
        error_msg = f"{type(exc).__name__}: {exc}"
    elapsed = time.perf_counter() - t0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    gc.collect()
    return BenchResult(
        name=name,
        category=category,
        elapsed_ms=round(elapsed * 1000, 2),
        mem_peak_kb=round(peak / 1024, 1),
        success=success,
        error=error_msg,
        iterations=repeat,
    )


# ── Agent benchmarks ──────────────────────────────────────────────

async def bench_product_agent() -> BenchResult:
    from Services.agents.product import ProductAgent
    from Services.agents.base import AgentContext
    from Database.connection import async_session_factory

    agent = ProductAgent()
    async with async_session_factory() as session:
        ctx = AgentContext(session=session)
        t0 = time.perf_counter()
        try:
            await agent.execute(ctx, url="https://shopee.co.id/product/bench-12345")
        except Exception as exc:
            elapsed = time.perf_counter() - t0
            return BenchResult("ProductAgent", "agent", round(elapsed * 1000, 2), 0, False, f"{type(exc).__name__}: {exc}")
        elapsed = time.perf_counter() - t0
        _, peak = tracemalloc.get_traced_memory()
        return BenchResult("ProductAgent", "agent", round(elapsed * 1000, 2), round(peak / 1024, 1))


async def bench_review_agent() -> BenchResult:
    from Services.agents.review import ReviewAgent
    from Services.agents.base import AgentContext
    from Database.connection import async_session_factory

    agent = ReviewAgent()
    async with async_session_factory() as session:
        ctx = AgentContext(session=session)
        t0 = time.perf_counter()
        try:
            await agent.execute(ctx, product_id="bench-prod-1")
        except Exception as exc:
            elapsed = time.perf_counter() - t0
            return BenchResult("ReviewAgent", "agent", round(elapsed * 1000, 2), 0, False, f"{type(exc).__name__}: {exc}")
        elapsed = time.perf_counter() - t0
        _, peak = tracemalloc.get_traced_memory()
        return BenchResult("ReviewAgent", "agent", round(elapsed * 1000, 2), round(peak / 1024, 1))


async def bench_content_agent() -> BenchResult:
    from Services.agents.content import ContentAgent
    from Services.agents.base import AgentContext
    from Database.connection import async_session_factory

    agent = ContentAgent()
    async with async_session_factory() as session:
        ctx = AgentContext(session=session)
        t0 = time.perf_counter()
        try:
            await agent.execute(ctx, product_id="bench-prod-1", category="elektronik")
        except Exception as exc:
            elapsed = time.perf_counter() - t0
            return BenchResult("ContentAgent", "agent", round(elapsed * 1000, 2), 0, False, f"{type(exc).__name__}: {exc}")
        elapsed = time.perf_counter() - t0
        _, peak = tracemalloc.get_traced_memory()
        return BenchResult("ContentAgent", "agent", round(elapsed * 1000, 2), round(peak / 1024, 1))


async def bench_offer_agent() -> BenchResult:
    from Services.agents.offer import OfferAgent
    from Services.agents.base import AgentContext
    from Database.connection import async_session_factory
    from MCP.schemas import AnalyzeProductOutput

    product = AnalyzeProductOutput(
        product_id="bench-1", title="Bench Product", price=150000.0,
        url="https://shopee.co.id/bench-12345",
    )
    agent = OfferAgent()
    async with async_session_factory() as session:
        ctx = AgentContext(session=session)
        t0 = time.perf_counter()
        try:
            await agent.execute(ctx, product=product)
        except Exception as exc:
            elapsed = time.perf_counter() - t0
            return BenchResult("OfferAgent", "agent", round(elapsed * 1000, 2), 0, False, f"{type(exc).__name__}: {exc}")
        elapsed = time.perf_counter() - t0
        _, peak = tracemalloc.get_traced_memory()
        return BenchResult("OfferAgent", "agent", round(elapsed * 1000, 2), round(peak / 1024, 1))


# ── MCP tool benchmarks ───────────────────────────────────────────

async def bench_health() -> BenchResult:
    from MCP.tools.health import health
    return await _bench("health", "mcp_tool", health)


async def bench_generate_offer() -> BenchResult:
    from MCP.tools.generate_offer import generate_offer
    from MCP.schemas import GenerateOfferInput, AnalyzeProductOutput

    product = AnalyzeProductOutput(
        product_id="bench-1", title="Benchmark Product", price=150000.0,
        url="https://shopee.co.id/bench-12345",
    )
    return await _bench(
        "generate_offer", "mcp_tool",
        generate_offer,
        GenerateOfferInput(product_id="bench-1", product_analysis=product),
    )


async def bench_generate_hooks() -> BenchResult:
    from MCP.tools.generate_hooks import generate_hooks
    from MCP.schemas import GenerateHooksInput, GenerateOfferOutput

    offer = GenerateOfferOutput(
        product_id="bench-1", primary_angle="Social Proof",
        value_proposition="Best product in class",
    )
    return await _bench(
        "generate_hooks", "mcp_tool",
        generate_hooks,
        GenerateHooksInput(product_id="bench-1", offer_strategy=offer, count=10),
    )


async def bench_generate_script() -> BenchResult:
    from MCP.tools.generate_script import generate_script
    from MCP.schemas import GenerateScriptInput, GenerateOfferOutput, Hook

    offer = GenerateOfferOutput(
        product_id="bench-1", primary_angle="Social Proof",
        value_proposition="Best product in class",
    )
    hooks = [
        Hook(hook=f"Bench hook {i}", type="curiosity", predicted_ctr="high")
        for i in range(5)
    ]
    return await _bench(
        "generate_script", "mcp_tool",
        generate_script,
        GenerateScriptInput(product_id="bench-1", hooks=hooks, offer_strategy=offer, count=5),
    )


# ── Full pipeline benchmark ───────────────────────────────────────

async def bench_full_pipeline() -> BenchResult:
    from MCP.tools.create_affiliate_package import create_affiliate_package
    from MCP.schemas import CreateAffiliatePackageInput

    tracemalloc.start()
    gc.collect()
    t0 = time.perf_counter()
    error_msg = ""
    success = True
    try:
        await create_affiliate_package(
            CreateAffiliatePackageInput(url="https://shopee.co.id/bench-product-12345")
        )
    except Exception as exc:
        success = False
        error_msg = f"{type(exc).__name__}: {exc}"
    elapsed = time.perf_counter() - t0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    gc.collect()
    return BenchResult(
        name="create_affiliate_package",
        category="full_pipeline",
        elapsed_ms=round(elapsed * 1000, 2),
        mem_peak_kb=round(peak / 1024, 1),
        success=success,
        error=error_msg,
    )


# ── Process memory snapshot ───────────────────────────────────────

def memory_snapshot() -> dict[str, float]:
    """Current process memory in MB via /proc or psutil."""
    try:
        import psutil
        proc = psutil.Process()
        m = proc.memory_info()
        return {"rss_mb": round(m.rss / 1024 / 1024, 1), "vms_mb": round(m.vms / 1024 / 1024, 1)}
    except ImportError:
        pass
    # fallback: /proc/self/status
    try:
        with open(f"/proc/{os.getpid()}/status") as f:
            data: dict[str, float] = {}
            for line in f:
                if line.startswith("VmRSS:"):
                    data["rss_mb"] = round(float(line.split()[1]) / 1024, 1)
                elif line.startswith("VmSize:"):
                    data["vms_mb"] = round(float(line.split()[1]) / 1024, 1)
            return data
    except Exception:
        return {"rss_mb": -1.0, "vms_mb": -1.0}


# ── Table printer ─────────────────────────────────────────────────

def print_table(results: list[BenchResult]) -> None:
    headers = ["Name", "Category", "Time (ms)", "Avg (ms)", "Peak Mem (KB)", "Status"]
    widths = [28, 14, 14, 14, 16, 10]

    hr = "+" + "+".join("-" * w for w in widths) + "+"
    def row(vals: list[str]) -> str:
        return "|" + "|".join(f" {v:<{w - 2}} " for v, w in zip(vals, widths)) + "|"

    print()
    print("=" * (sum(widths) + len(widths) + 1))
    print("  TITAN AIO PERFORMANCE BENCHMARK")
    print("=" * (sum(widths) + len(widths) + 1))
    print(hr)
    print(row(headers))
    print(hr)

    for r in results:
        status = "OK" if r.success else "FAIL"
        print(row([
            r.name,
            r.category,
            f"{r.elapsed_ms:.1f}",
            f"{r.avg_ms:.1f}",
            f"{r.mem_peak_kb:.0f}",
            status,
        ]))
        if r.error:
            print(f"  \\_ {r.error[:80]}")

    print(hr)

    total_time = sum(r.elapsed_ms for r in results)
    total_peak = max((r.mem_peak_kb for r in results), default=0)
    failed = sum(1 for r in results if not r.success)
    print(f"  Total time: {total_time:.1f} ms | Peak mem: {total_peak:.0f} KB | Failed: {failed}/{len(results)}")

    mem = memory_snapshot()
    if mem.get("rss_mb", -1) > 0:
        print(f"  Process RSS: {mem['rss_mb']:.1f} MB | VMS: {mem.get('vms_mb', 'N/A')} MB")
    print()


# ── Benchmark registry ────────────────────────────────────────────

BENCHMARKS: list[tuple[str, str, Callable[..., Coroutine[Any, Any, BenchResult]]]] = [
    ("health",              "mcp_tool",      bench_health),
    ("generate_offer",      "mcp_tool",      bench_generate_offer),
    ("generate_hooks",      "mcp_tool",      bench_generate_hooks),
    ("generate_script",     "mcp_tool",      bench_generate_script),
    ("ProductAgent",        "agent",         bench_product_agent),
    ("ReviewAgent",         "agent",         bench_review_agent),
    ("ContentAgent",        "agent",         bench_content_agent),
    ("OfferAgent",          "agent",         bench_offer_agent),
    ("full_pipeline",       "full_pipeline", bench_full_pipeline),
]


async def run_benchmarks(repeat: int = 1) -> list[BenchResult]:
    # Ensure tables exist in test DB (import models so metadata is populated)
    from Database.connection import init_db
    from Database import models  # noqa: F401 — registers all ORM tables
    await init_db()

    results: list[BenchResult] = []
    for name, cat, fn in BENCHMARKS:
        print(f"  {name:<28}", end="", flush=True)
        if repeat > 1:
            result = await _bench(name, cat, fn, repeat=repeat)
        else:
            result = await fn()
        print(f"{result.elapsed_ms:>8.1f} ms  {'OK' if result.success else 'FAIL'}")
        results.append(result)
    return results


def save_results(results: list[BenchResult], path: Path) -> None:
    data = {
        "benchmarks": [
            {
                "name": r.name,
                "category": r.category,
                "elapsed_ms": r.elapsed_ms,
                "avg_ms": r.avg_ms,
                "mem_peak_kb": r.mem_peak_kb,
                "success": r.success,
                "error": r.error,
                "iterations": r.iterations,
            }
            for r in results
        ],
        "summary": {
            "total_time_ms": round(sum(r.elapsed_ms for r in results), 2),
            "total_benchmarks": len(results),
            "passed": sum(1 for r in results if r.success),
            "failed": sum(1 for r in results if not r.success),
            "memory": memory_snapshot(),
        },
    }
    path.write_text(json.dumps(data, indent=2))
    print(f"  Results saved to {path}")


# ── Main ──────────────────────────────────────────────────────────

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Titan AIO performance benchmarks")
    parser.add_argument("--repeat", type=int, default=1, help="Repeat count per benchmark")
    parser.add_argument("--json", action="store_true", help="JSON output only")
    parser.add_argument("--output", type=str, default=str(Path(__file__).resolve().parent / "benchmarks.json"), help="Output JSON path")
    args = parser.parse_args()

    print("\nTitan AIO Performance Benchmark")
    print(f"Repeat: {args.repeat} | Python {sys.version.split()[0]}")
    print("-" * 50)

    results = asyncio.run(run_benchmarks(repeat=args.repeat))

    if not args.json:
        print_table(results)

    out_path = Path(args.output)
    save_results(results, out_path)

    if args.json:
        print(Path(args.output).read_text())

    if any(not r.success for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
