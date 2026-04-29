from datetime import datetime, timezone

from app.core.security import get_password_hash
from app.modules.auth.models import User
from app.modules.news.repository import NewsRepository
from app.modules.news.schemas import NewsCreateInternal
from app.modules.news.service import NewsService
from app.modules.sources.models import Category, InformationSource, RSSChannel


def test_create_news_accepts_long_external_id(db):
    user = User(
        email="long-external-id@example.com",
        first_name="Long",
        last_name="ExternalId",
        organization="NewsRadar",
        hashed_password=get_password_hash("Password123!"),
        role="gestor",
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    category = (
        db.query(Category).filter(Category.name == "science_technology").first()
    )
    if category is None:
        category = Category(name="science_technology", source="IPTC")
        db.add(category)
        db.commit()
        db.refresh(category)

    medium = InformationSource(name="BBC", url="https://example.com/")
    db.add(medium)
    db.commit()
    db.refresh(medium)

    channel = RSSChannel(
        url="https://example.com/rss/technology.xml",
        category_id=category.id,
        information_source_id=medium.id,
        name="Technology",
        is_active=True,
    )
    db.add(channel)
    db.commit()
    db.refresh(channel)

    long_external_id = "https://example.com/item/" + ("x" * 600)

    news_service = NewsService(NewsRepository(db))
    created = news_service.create_news_from_crawler(
        NewsCreateInternal(
            source_id=channel.id,
            title="Very long external id article",
            link="https://example.com/articles/long-external-id",
            summary="Regression test for long feed identifiers.",
            published_at=datetime.now(timezone.utc),
            category="science_technology",
            classification_origin="source",
            language="en",
            author="NewsRadar Test",
            external_id=long_external_id,
        )
    )

    assert created.external_id == long_external_id
