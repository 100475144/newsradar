"""Repositorio del módulo news: irá el acceso a datos de noticias (consultas, inserciones y búsquedas)."""
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import News


class NewsRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, news: News) -> News:
        self.db.add(news)
        self.db.commit()
        self.db.refresh(news)
        return news

    def get_by_id(self, news_id: int) -> Optional[News]:
        stmt = select(News).where(News.id == news_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def list(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
        source_id: int | None = None,
        category: str | None = None,
    ) -> list[News]:
        stmt = select(News).order_by(News.published_at.desc(), News.id.desc())

        if source_id is not None:
            stmt = stmt.where(News.source_id == source_id)

        if category:
            stmt = stmt.where(News.category == category)

        stmt = stmt.offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def count(
        self,
        *,
        source_id: int | None = None,
        category: str | None = None,
    ) -> int:
        stmt = select(func.count(News.id)).select_from(News)

        if source_id is not None:
            stmt = stmt.where(News.source_id == source_id)

        if category:
            stmt = stmt.where(News.category == category)

        return int(self.db.execute(stmt).scalar_one())

    def count_by_source(self, source_id: int) -> int:
        stmt = select(func.count(News.id)).where(News.source_id == source_id)
        return int(self.db.execute(stmt).scalar_one())

    def get_by_external_id(self, *, source_id: int | None, external_id: str) -> Optional[News]:
        stmt = select(News).where(
            News.external_id == external_id,
            News.source_id == source_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_link(self, link: str) -> Optional[News]:
        stmt = select(News).where(News.link == link)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_content_hash(self, content_hash: str) -> Optional[News]:
        stmt = select(News).where(News.content_hash == content_hash)
        return self.db.execute(stmt).scalar_one_or_none()

    def count_total(self) -> int:
        stmt = select(func.count(News.id))
        return int(self.db.execute(stmt).scalar_one())

    def count_by_category(self) -> list[dict]:
        stmt = (
            select(News.category, func.count(News.id).label("count"))
            .where(News.category.isnot(None))
            .group_by(News.category)
            .order_by(func.count(News.id).desc())
        )
        rows = self.db.execute(stmt).all()
        return [{"category": r.category, "count": r.count} for r in rows]

    def word_frequencies(self, category: str | None = None, limit: int = 50) -> list[dict]:
        stmt = select(News.title).where(News.title.isnot(None))
        if category:
            stmt = stmt.where(News.category == category)
        titles = [row[0] for row in self.db.execute(stmt).all()]

        freq: dict[str, int] = {}
        stop = {
            "a", "an", "the", "and", "or", "but", "in", "on", "at", "to",
            "for", "of", "with", "by", "from", "is", "it", "as", "be",
            "was", "are", "been", "its", "this", "that", "not", "has",
            "have", "had", "will", "would", "can", "could", "may",
            "de", "la", "el", "en", "y", "los", "las", "del", "un",
            "una", "que", "por", "con", "para", "se", "su", "al", "es",
            "lo", "no", "más", "ya", "han", "ha", "son", "sobre", "como",
        }
        for title in titles:
            for word in title.lower().split():
                cleaned = "".join(c for c in word if c.isalnum())
                if len(cleaned) > 2 and cleaned not in stop:
                    freq[cleaned] = freq.get(cleaned, 0) + 1

        sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [{"text": w, "value": v} for w, v in sorted_words]