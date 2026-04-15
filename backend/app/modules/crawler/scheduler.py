import asyncio
import logging
import os
from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.news.repository import NewsRepository
from app.modules.news.service import NewsService
from app.modules.sources.models import Source

from .service import CrawlerService

logger = logging.getLogger(__name__)


class CrawlerScheduler:
    def __init__(
        self,
        db_factory: Callable[[], Session],
        interval_seconds: int = 300,
        run_on_startup: bool = True,
    ):
        self.db_factory = db_factory
        self.interval_seconds = interval_seconds
        self.run_on_startup = run_on_startup
        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()

    def start(self) -> None:
        if self._task and not self._task.done():
            logger.info("Crawler scheduler already running")
            return

        logger.info(
            "Starting crawler scheduler with interval=%s seconds",
            self.interval_seconds,
        )
        self._stop_event = asyncio.Event()
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        if not self._task:
            return

        logger.info("Stopping crawler scheduler")
        self._stop_event.set()

        try:
            await self._task
        except asyncio.CancelledError:
            logger.info("Crawler scheduler task cancelled")
        finally:
            self._task = None

    async def trigger_once(self) -> None:
        await asyncio.to_thread(self._run_cycle)

    async def _run_loop(self) -> None:
        try:
            if self.run_on_startup:
                await asyncio.to_thread(self._run_cycle)

            while not self._stop_event.is_set():
                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(),
                        timeout=self.interval_seconds,
                    )
                except asyncio.TimeoutError:
                    await asyncio.to_thread(self._run_cycle)

        except Exception:
            logger.exception("Unexpected error in crawler scheduler loop")

    def _run_cycle(self) -> None:
        logger.info("Crawler scheduler cycle started")

        db = self.db_factory()
        try:
            user_ids = self._get_user_ids_with_active_sources(db)

            if not user_ids:
                logger.info("No active sources found for any user")
                return

            for user_id in user_ids:
                try:
                    news_repository = NewsRepository(db)
                    news_service = NewsService(news_repository)
                    crawler_service = CrawlerService(db, news_service)

                    results = crawler_service.crawl_all_active_sources(user_id)

                    processed_sources = len(results)
                    stored_items = sum(result.stored_items for result in results)
                    skipped_items = sum(result.duplicates_skipped for result in results)

                    logger.info(
                        "Crawler run for user_id=%s finished: processed_sources=%s stored_items=%s duplicates_skipped=%s",
                        user_id,
                        processed_sources,
                        stored_items,
                        skipped_items,
                    )

                except Exception:
                    logger.exception(
                        "Crawler failed for user_id=%s",
                        user_id,
                    )
                    db.rollback()

        except Exception:
            logger.exception("Crawler scheduler cycle failed")
            db.rollback()
        finally:
            db.close()

        logger.info("Crawler scheduler cycle finished")

    @staticmethod
    def _get_user_ids_with_active_sources(db: Session) -> list[int]:
        stmt = (
            select(Source.created_by)
            .where(Source.is_active.is_(True))
            .distinct()
        )
        return list(db.execute(stmt).scalars().all())


def get_crawler_interval_seconds() -> int:
    raw = os.getenv("CRAWLER_INTERVAL_SECONDS", "300")
    try:
        value = int(raw)
        return max(30, value)
    except ValueError:
        return 300