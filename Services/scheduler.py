"""Simple scheduler for autonomous posting cycles.

No external dependencies. Uses asyncio for timing.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from titan.autonomous_loop import AutonomousLoop

logger = logging.getLogger("titan.scheduler")


class PostingScheduler:
    """Schedule autonomous campaign cycles at fixed intervals."""

    def __init__(self, interval_minutes: int = 60):
        self.interval = interval_minutes
        self.loop = AutonomousLoop(use_scraper=True)
        self._running = False
        self._stats = {"cycles": 0, "campaigns": 0, "errors": 0, "started_at": None}

    async def start(self, max_cycles: int = 0) -> dict:
        self._running = True
        self._stats["started_at"] = datetime.utcnow().isoformat()
        cycle = 0

        print(f"\n{'=' * 50}")
        print(f"⏰ SCHEDULER STARTED — interval {self.interval} min")
        print(f"{'=' * 50}")

        while self._running and (max_cycles == 0 or cycle < max_cycles):
            cycle += 1
            print(f"\n📡 Cycle #{cycle} @ {datetime.now().strftime('%H:%M:%S')}")

            try:
                result = await self.loop.run_once()
                if result.get("status") == "complete":
                    self._stats["cycles"] += 1
                    self._stats["campaigns"] += 1
            except Exception as e:
                self._stats["errors"] += 1
                print(f"❌ Cycle failed: {e}")

            if self._running and (max_cycles == 0 or cycle < max_cycles):
                print(f"⏳ Next cycle in {self.interval} min...")
                await asyncio.sleep(self.interval * 60)

        self._running = False
        self._stats["ended_at"] = datetime.utcnow().isoformat()
        print(f"\n{'=' * 50}")
        print("🏁 SCHEDULER COMPLETE")
        print(f"{'=' * 50}")
        return self._stats

    def stop(self):
        self._running = False


async def run_scheduler(interval_minutes: int = 60, max_cycles: int = 0):
    sched = PostingScheduler(interval_minutes=interval_minutes)
    return await sched.start(max_cycles=max_cycles)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=int, default=60, help="Menit antar siklus")
    parser.add_argument("--max-cycles", type=int, default=0, help="Max siklus (0=tak terbatas)")
    args = parser.parse_args()
    asyncio.run(run_scheduler(interval_minutes=args.interval, max_cycles=args.max_cycles))
