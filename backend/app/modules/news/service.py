"""Servicio del módulo news: se implementará la lógica de negocio relacionada con noticias."""
import hashlib
from urllib.parse import urlsplit, urlunsplit

from .models import News
from .repository import NewsRepository
from .schemas import NewsCreateInternal
from app.modules.alerts.matching import process_alerts_for_news


class NewsService:
    def __init__(self, repository: NewsRepository):
        self.repository = repository

    def list_news(
        self,
        *,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
        source_id: int | None = None,
        category: str | None = None,
    ):
        items = self.repository.list(
            skip=skip,
            limit=limit,
            source_id=source_id,
            category=category,
        )
        total = self.repository.count(
            source_id=source_id,
            category=category,
        )
        return {"items": items, "total": total}

    def get_news(self, news_id: int):
        return self.repository.get_by_id(news_id)

    def create_news_from_crawler(self, payload: NewsCreateInternal) -> News:
        normalized_link = self._normalize_link(payload.link)
        content_hash = payload.content_hash or self._build_content_hash(
            source_id=payload.source_id,
            title=payload.title,
            link=normalized_link,
            published_at=payload.published_at.isoformat() if payload.published_at else None,
        )

        if payload.external_id:
            existing = self.repository.get_by_external_id(
                source_id=payload.source_id,
                external_id=payload.external_id,
            )
            if existing:
                return existing

        existing = self.repository.get_by_link(normalized_link)
        if existing:
            return existing

        existing = self.repository.get_by_content_hash(content_hash)
        if existing:
            return existing

        news = News(
            source_id=payload.source_id,
            title=payload.title.strip(),
            link=normalized_link,
            summary=payload.summary,
            published_at=payload.published_at,
            category=payload.category,
            classification_origin=payload.classification_origin,
            language=payload.language,
            author=payload.author,
            external_id=payload.external_id,
            content_hash=content_hash,
        )
        
        created_news = self.repository.create(news)
        process_alerts_for_news(self.repository.db, created_news)
        return created_news
        
    @staticmethod
    def _normalize_link(link: str) -> str:
        parts = urlsplit(link.strip())
        return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))

    @staticmethod
    def _build_content_hash(
        *,
        source_id: int | None,
        title: str,
        link: str,
        published_at: str | None,
    ) -> str:
        raw = f"{source_id}|{title.strip().lower()}|{link}|{published_at or ''}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
