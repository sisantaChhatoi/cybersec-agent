"""Periodic fraud-graph rebuild via APScheduler.

pipeline.run() is synchronous, so it's offloaded to a thread-pool executor
to keep the rebuild off the async event loop.
"""

from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from server.graph.pipeline import run
from shared.config import settings

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


async def _rebuild() -> None:
    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, run)
        logger.info("Graph rebuild complete: %s", result)
    except Exception:
        logger.exception("Graph rebuild failed — previous snapshot retained")


def start_scheduler() -> None:
    global _scheduler
    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        _rebuild,
        "interval",
        hours=settings.graph_rebuild_interval_hours,
        id="graph_rebuild",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info(
        "Graph rebuild scheduler started (interval: %dh)",
        settings.graph_rebuild_interval_hours,
    )


def stop_scheduler() -> None:
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
