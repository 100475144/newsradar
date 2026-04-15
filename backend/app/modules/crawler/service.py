"""Servicio del módulo crawler: se implementará la lógica de crawling, scraping y procesamiento inicial de fuentes."""
from datetime import datetime

import feedparser
from sqlalchemy.orm import Session

from app.modules.news.schemas import NewsCreateInternal
from app.modules.news.service import NewsService
from app.modules.sources.repository import SourceRepository

from .schemas import CrawlResult, ParsedFeedItem, SourceStub


class CrawlerService:
    def __init__(self, db: Session, news_service: NewsService):
        self.db = db
        self.news_service = news_service
        self.source_repository = SourceRepository(db)

    def get_active_sources(self, user_id: int) -> list[SourceStub]:
        user_sources = self.source_repository.list_by_owner(user_id)
        active_sources = [source for source in user_sources if source.is_active]

        return [
            SourceStub(
                id=source.id,
                name=source.name,
                url=source.url,
                category=getattr(source, "category", None),
                is_active=source.is_active,
            )
            for source in active_sources
        ]

    def crawl_all_active_sources(self, user_id: int) -> list[CrawlResult]:
        results: list[CrawlResult] = []
        for source in self.get_active_sources(user_id):
            results.append(self.crawl_source(source))
        return results

    def crawl_source(self, source: SourceStub) -> CrawlResult:
        feed = feedparser.parse(source.url)

        fetched_items = 0
        stored_items = 0
        duplicates_skipped = 0

        for entry in feed.entries:
            fetched_items += 1

            item = self._parse_entry(entry, source)
            payload = NewsCreateInternal(
                source_id=source.id,
                title=item.title,
                link=item.link,
                summary=item.summary,
                published_at=item.published_at,
                category=item.category or source.category,
                author=item.author,
                external_id=item.external_id,
            )

            before = self.news_service.repository.count_by_source(source.id)
            self.news_service.create_news_from_crawler(payload)
            after = self.news_service.repository.count_by_source(source.id)

            if after > before:
                stored_items += 1
            else:
                duplicates_skipped += 1

        return CrawlResult(
            source_id=source.id,
            source_name=source.name,
            fetched_items=fetched_items,
            stored_items=stored_items,
            duplicates_skipped=duplicates_skipped,
        )

    def _parse_entry(self, entry, source: SourceStub) -> ParsedFeedItem:
        published_at = None
        if getattr(entry, "published_parsed", None):
            published_at = datetime(*entry.published_parsed[:6])

        return ParsedFeedItem(
            title=getattr(entry, "title", "").strip(),
            link=getattr(entry, "link", "").strip(),
            summary=getattr(entry, "summary", None),
            published_at=published_at,
            author=getattr(entry, "author", None),
            external_id=getattr(entry, "id", None),
            category=self._extract_category(entry) or source.category,
        )

    @staticmethod
    def _extract_category(entry) -> str | None:
        tags = getattr(entry, "tags", None)
        if tags and len(tags) > 0:
            term = getattr(tags[0], "term", None)
            if term:
                return str(term)
        return None