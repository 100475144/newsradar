"""Crawler scheduler basado en expresiones cron via APScheduler."""

import logging
import os
from collections.abc import Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from app.modules.news.repository import NewsRepository
from app.modules.news.service import NewsService

from .service import CrawlerService

logger = logging.getLogger(__name__)


class CrawlerScheduler:
    """Ejecuta el ciclo de crawling según una expresión cron configurable."""

    def __init__(
        self,
        db_factory: Callable[[], Session],
        cron_expression: str = "*/5 * * * *",
        run_on_startup: bool = True,
    ):
        self.db_factory = db_factory
        self.cron_expression = cron_expression
        self.run_on_startup = run_on_startup
        self._scheduler = AsyncIOScheduler()

    def start(self) -> None:
        trigger = CronTrigger.from_crontab(self.cron_expression)

        self._scheduler.add_job(
            self._run_cycle_async,
            trigger=trigger,
            id="crawler_cycle",
            name="RSS Crawler Cycle",
            replace_existing=True,
        )

        self._scheduler.start()
        logger.info(
            "Crawler scheduler started with cron expression: %s",
            self.cron_expression,
        )

        if self.run_on_startup:
            self._scheduler.add_job(
                self._run_cycle_async,
                id="crawler_startup",
                name="RSS Crawler Startup",
            )

    async def stop(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("Crawler scheduler stopped")

    async def trigger_once(self) -> None:
        await self._run_cycle_async()

    async def _run_cycle_async(self) -> None:
        import asyncio
        await asyncio.to_thread(self._run_cycle)

    def _run_cycle(self) -> None:
        logger.info("Crawler scheduler cycle started")

        db = self.db_factory()
        try:
            news_repository = NewsRepository(db)
            news_service = NewsService(news_repository)
            crawler_service = CrawlerService(db, news_service)

            results = crawler_service.crawl_all_active_sources()

            processed_sources = len(results)
            stored_items = sum(result.stored_items for result in results)
            skipped_items = sum(result.duplicates_skipped for result in results)

            logger.info(
                "Crawler global run finished: processed_sources=%s stored_items=%s duplicates_skipped=%s",
                processed_sources,
                stored_items,
                skipped_items,
            )
        except Exception:
            logger.exception("Crawler scheduler cycle failed")
            db.rollback()
        finally:
            db.close()

        logger.info("Crawler scheduler cycle finished")


def get_crawler_cron_expression() -> str:
    return os.getenv("CRAWLER_CRON_EXPRESSION", "*/5 * * * *")
