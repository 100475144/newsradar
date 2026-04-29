"""Tests del crawler (TS5).

Cubren los tres escenarios pedidos en el reparto:
- éxito: feed con N items → N noticias creadas
- error: feed inaccesible / malformado / vacío → el crawler no rompe
- dedup: mismo feed dos veces → no se duplican filas en news
"""

from __future__ import annotations

import time
from types import SimpleNamespace
from unittest.mock import patch

from app.modules.crawler.schemas import SourceStub
from app.modules.crawler.service import CrawlerService
from app.modules.news.models import News
from app.modules.news.repository import NewsRepository
from app.modules.news.service import NewsService
from app.modules.sources.models import Category, InformationSource, RSSChannel
from app.tests.helpers import create_test_user


# ─────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────


def _make_feed(entries: list[dict]):
    """Construye un objeto compatible con ``feedparser.parse`` con N entries."""
    parsed_entries = []
    for entry in entries:
        published_struct = time.strptime("2026-04-29T10:00:00", "%Y-%m-%dT%H:%M:%S")
        parsed_entries.append(
            SimpleNamespace(
                title=entry.get("title", ""),
                link=entry.get("link", ""),
                summary=entry.get("summary"),
                published_parsed=entry.get("published_parsed", published_struct),
                author=entry.get("author"),
                id=entry.get("id"),
                tags=entry.get("tags", []),
                language=entry.get("language"),
            )
        )
    return SimpleNamespace(
        entries=parsed_entries,
        feed=SimpleNamespace(language="en"),
    )


def _ensure_seed_entities(db):
    """Garantiza Category + InformationSource + RSSChannel para los tests."""
    cat = db.query(Category).filter(Category.name == "science_technology").first()
    if cat is None:
        cat = Category(name="science_technology", source="IPTC")
        db.add(cat)
        db.commit()
        db.refresh(cat)

    medium = InformationSource(name="TestMedium", url="https://test.example/")
    db.add(medium)
    db.commit()
    db.refresh(medium)

    channel = RSSChannel(
        url="https://test.example/feed.rss",
        category_id=cat.id,
        information_source_id=medium.id,
        name="TestChannel",
        is_active=True,
    )
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return cat, medium, channel


# ─────────────────────────────────────────────────────────────────────
# Éxito
# ─────────────────────────────────────────────────────────────────────


def test_crawl_success_creates_news_rows(db):
    create_test_user(db, email="crawler-ok@example.com")
    _, _, channel = _ensure_seed_entities(db)
    source_stub = SourceStub(
        id=channel.id,
        medium_name="TestMedium",
        name="TestChannel",
        url=channel.url,
        category="science_technology",
        is_active=True,
    )

    fake_feed = _make_feed([
        {
            "title": "AI breakthrough today",
            "link": "https://test.example/articles/1",
            "summary": "Some summary 1",
            "id": "ext-1",
        },
        {
            "title": "Quantum advance",
            "link": "https://test.example/articles/2",
            "summary": "Some summary 2",
            "id": "ext-2",
        },
        {
            "title": "Robotics milestone",
            "link": "https://test.example/articles/3",
            "summary": "Some summary 3",
            "id": "ext-3",
        },
    ])

    service = CrawlerService(db, NewsService(NewsRepository(db)))

    with patch("app.modules.crawler.service.feedparser.parse", return_value=fake_feed):
        result = service.crawl_source(source_stub)

    assert result.fetched_items == 3
    assert result.stored_items == 3
    assert result.duplicates_skipped == 0

    rows = db.query(News).filter(News.source_id == channel.id).all()
    assert len(rows) == 3
    assert {row.external_id for row in rows} == {"ext-1", "ext-2", "ext-3"}


# ─────────────────────────────────────────────────────────────────────
# Errores / casos límite
# ─────────────────────────────────────────────────────────────────────


def test_crawl_handles_empty_feed(db):
    create_test_user(db, email="crawler-empty@example.com")
    _, _, channel = _ensure_seed_entities(db)
    source_stub = SourceStub(
        id=channel.id,
        medium_name="TestMedium",
        name="TestChannel",
        url=channel.url,
        category="science_technology",
    )

    fake_feed = _make_feed([])

    service = CrawlerService(db, NewsService(NewsRepository(db)))
    with patch("app.modules.crawler.service.feedparser.parse", return_value=fake_feed):
        result = service.crawl_source(source_stub)

    assert result.fetched_items == 0
    assert result.stored_items == 0
    assert result.duplicates_skipped == 0


def test_crawl_handles_malformed_entries_without_crashing(db):
    """Entries sin título o sin link no deben tumbar el ciclo."""
    create_test_user(db, email="crawler-malformed@example.com")
    _, _, channel = _ensure_seed_entities(db)
    source_stub = SourceStub(
        id=channel.id,
        medium_name="TestMedium",
        name="TestChannel",
        url=channel.url,
        category="science_technology",
    )

    fake_feed = _make_feed([
        {"title": "", "link": "https://test.example/x", "id": "x"},  # title vacío
        {"title": "Good item", "link": "https://test.example/good", "id": "good"},
    ])

    service = CrawlerService(db, NewsService(NewsRepository(db)))
    with patch("app.modules.crawler.service.feedparser.parse", return_value=fake_feed):
        # No debe levantar excepción
        result = service.crawl_source(source_stub)

    # El item bien formado se almacena; el vacío se descarta o cuenta como inválido
    rows = db.query(News).filter(News.source_id == channel.id).all()
    assert any(row.title == "Good item" for row in rows)
    assert result.fetched_items == 2


def test_crawl_handles_feed_with_no_entries_attribute(db):
    """Feed que no expone ``entries`` (HTTP error en feedparser) → 0 news."""
    create_test_user(db, email="crawler-noattr@example.com")
    _, _, channel = _ensure_seed_entities(db)
    source_stub = SourceStub(
        id=channel.id,
        medium_name="TestMedium",
        name="TestChannel",
        url=channel.url,
        category="science_technology",
    )

    # Cuando feedparser falla, devuelve un objeto con ``entries=[]`` y bozo flag.
    broken_feed = SimpleNamespace(entries=[], feed=SimpleNamespace(language=None), bozo=1)

    service = CrawlerService(db, NewsService(NewsRepository(db)))
    with patch("app.modules.crawler.service.feedparser.parse", return_value=broken_feed):
        result = service.crawl_source(source_stub)

    assert result.fetched_items == 0
    assert result.stored_items == 0


# ─────────────────────────────────────────────────────────────────────
# Deduplicación
# ─────────────────────────────────────────────────────────────────────


def test_crawl_does_not_create_duplicates_on_repeat(db):
    """Pasar el mismo feed dos veces no genera duplicados."""
    create_test_user(db, email="crawler-dedup@example.com")
    _, _, channel = _ensure_seed_entities(db)
    source_stub = SourceStub(
        id=channel.id,
        medium_name="TestMedium",
        name="TestChannel",
        url=channel.url,
        category="science_technology",
    )

    fake_feed = _make_feed([
        {
            "title": "Repeating story",
            "link": "https://test.example/repeat/1",
            "summary": "Body",
            "id": "rep-1",
        },
        {
            "title": "Another repeating story",
            "link": "https://test.example/repeat/2",
            "summary": "Body 2",
            "id": "rep-2",
        },
    ])

    service = CrawlerService(db, NewsService(NewsRepository(db)))

    with patch("app.modules.crawler.service.feedparser.parse", return_value=fake_feed):
        first_run = service.crawl_source(source_stub)
        second_run = service.crawl_source(source_stub)

    assert first_run.stored_items == 2
    assert first_run.duplicates_skipped == 0
    assert second_run.stored_items == 0
    assert second_run.duplicates_skipped == 2

    rows = db.query(News).filter(News.source_id == channel.id).all()
    assert len(rows) == 2


def test_crawl_all_active_sources_iterates_active_only(db):
    """``crawl_all_active_sources`` solo procesa channels con is_active=True.

    Nota sobre aislamiento: otros tests de la misma sesión pueden haber
    sembrado canales (con ``commit`` dentro de la sesión transaccional).
    El test comprueba pertenencia (el activo está, el inactivo no), no
    longitud exacta de la lista de resultados.
    """
    create_test_user(db, email="crawler-active@example.com")
    cat, medium, active_channel = _ensure_seed_entities(db)

    inactive_channel = RSSChannel(
        url="https://test.example/inactive.rss",
        category_id=cat.id,
        information_source_id=medium.id,
        name="Inactive",
        is_active=False,
    )
    db.add(inactive_channel)
    db.commit()
    db.refresh(inactive_channel)

    service = CrawlerService(db, NewsService(NewsRepository(db)))

    fake_feed = _make_feed([
        {"title": "Active feed item", "link": "https://test.example/a/1", "id": "a-1"},
    ])
    with patch("app.modules.crawler.service.feedparser.parse", return_value=fake_feed):
        results = service.crawl_all_active_sources()

    result_ids = {r.source_id for r in results}
    assert active_channel.id in result_ids
    assert inactive_channel.id not in result_ids
