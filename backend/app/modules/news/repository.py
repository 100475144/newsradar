"""Repositorio del módulo news: irá el acceso a datos de noticias (consultas, inserciones y búsquedas)."""
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.sources.models import Source

from .models import News


class NewsRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, news: News) -> News:
        self.db.add(news)
        self.db.commit()
        self.db.refresh(news)
        return news

    def get_by_id_for_user(self, news_id: int, user_id: int) -> Optional[News]:
        stmt = (
            select(News)
            .join(Source, News.source_id == Source.id)
            .where(
                News.id == news_id,
                Source.created_by == user_id,
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_user(
        self,
        *,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
        source_id: int | None = None,
        category: str | None = None,
    ) -> list[News]:
        stmt = (
            select(News)
            .join(Source, News.source_id == Source.id)
            .where(Source.created_by == user_id)
            .order_by(News.published_at.desc(), News.id.desc())
        )

        if source_id is not None:
            stmt = stmt.where(News.source_id == source_id)

        if category:
            stmt = stmt.where(News.category == category)

        stmt = stmt.offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def count_for_user(
        self,
        *,
        user_id: int,
        source_id: int | None = None,
        category: str | None = None,
    ) -> int:
        stmt = (
            select(func.count(News.id))
            .select_from(News)
            .join(Source, News.source_id == Source.id)
            .where(Source.created_by == user_id)
        )

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