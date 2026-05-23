"""Tests del módulo ``news``.

Cubre:
* ``news/api.py`` — endpoints ``/news``, ``/news/{id}``, ``/news/stats``,
  ``/news/wordcloud``, ``/news/me/stats``, ``/news/me/wordcloud``.
* ``news/service.py`` — dedupe por ``external_id`` / ``link`` /
  ``content_hash``, normalización de link (strip query+fragment), wordcloud
  por usuario y global.
* ``news/repository.py`` — filtros (source_id, category), paginación,
  word_frequencies (stopwords ES/EN), count_total_for_user vía notifications.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.modules.news.models import News
from app.modules.news.repository import NewsRepository
from app.modules.news.schemas import NewsCreateInternal
from app.modules.news.service import NewsService
from app.modules.notifications.repository import NotificationRepository
from app.tests.helpers import auth_headers_for, create_test_user


# ── service: normalización y dedupe ─────────────────────────────────


def test_normalize_link_strips_query_and_fragment():
    out = NewsService._normalize_link(
        "  https://example.com/path?utm_source=foo#frag  "
    )
    assert out == "https://example.com/path"


def test_build_content_hash_is_deterministic():
    h1 = NewsService._build_content_hash(
        source_id=1, title="Hola", link="https://a.com/x", published_at="2024-01-01T00:00:00",
    )
    h2 = NewsService._build_content_hash(
        source_id=1, title="HOLA", link="https://a.com/x", published_at="2024-01-01T00:00:00",
    )
    # Title se minusculiza antes de hashear → mismo hash.
    assert h1 == h2


def test_build_content_hash_differs_for_different_inputs():
    h1 = NewsService._build_content_hash(
        source_id=1, title="A", link="https://a.com", published_at=None,
    )
    h2 = NewsService._build_content_hash(
        source_id=2, title="A", link="https://a.com", published_at=None,
    )
    assert h1 != h2


def test_service_create_dedupes_by_external_id(db):
    service = NewsService(NewsRepository(db))
    payload = NewsCreateInternal(
        title="A", link="https://x.com/a", external_id="ext-1", source_id=None,
    )
    n1 = service.create_news_from_crawler(payload)
    n2 = service.create_news_from_crawler(
        NewsCreateInternal(
            title="A copia", link="https://x.com/different",
            external_id="ext-1", source_id=None,
        )
    )
    assert n1.id == n2.id


def test_service_create_dedupes_by_normalized_link(db):
    service = NewsService(NewsRepository(db))
    n1 = service.create_news_from_crawler(NewsCreateInternal(
        title="A", link="https://x.com/b?utm=1", source_id=None,
    ))
    n2 = service.create_news_from_crawler(NewsCreateInternal(
        title="A", link="https://x.com/b?utm=2", source_id=None,
    ))
    # El link se normaliza a "https://x.com/b" antes de buscar duplicados.
    assert n1.id == n2.id


def test_service_create_dedupes_by_content_hash(db):
    service = NewsService(NewsRepository(db))
    n1 = service.create_news_from_crawler(NewsCreateInternal(
        title="Mismo título", link="https://x.com/one",
        content_hash="deadbeef" * 8, source_id=None,
    ))
    n2 = service.create_news_from_crawler(NewsCreateInternal(
        title="Otro título", link="https://x.com/two",
        content_hash="deadbeef" * 8, source_id=None,
    ))
    assert n1.id == n2.id


def test_service_get_news_returns_none_for_missing(db):
    service = NewsService(NewsRepository(db))
    assert service.get_news(999_999) is None


# ── repository: filtros, paginación, frequencies ────────────────────


def test_repository_count_and_list_filters(db):
    repo = NewsRepository(db)
    # Seed 3 noticias con diferente category.
    for i, cat in enumerate(["ciencia", "politica", "ciencia"]):
        news = News(
            title=f"Noticia {i}",
            link=f"https://example.com/news-{i}",
            category=cat,
            content_hash=f"hash-{i}",
            source_id=None,
        )
        db.add(news)
    db.commit()

    all_news = repo.list_all(limit=10)
    assert len(all_news) >= 3

    ciencia = repo.list_all(limit=10, category="ciencia")
    assert all(n.category == "ciencia" for n in ciencia)
    assert len(ciencia) == 2

    assert repo.count(category="ciencia") == 2
    assert repo.count(category="politica") == 1


def test_repository_pagination_skip_limit(db):
    repo = NewsRepository(db)
    for i in range(5):
        db.add(News(
            title=f"Pag {i}", link=f"https://p.example/{i}",
            content_hash=f"pag-{i}", source_id=None,
        ))
    db.commit()

    page1 = repo.list_all(skip=0, limit=2)
    page2 = repo.list_all(skip=2, limit=2)
    assert len(page1) == 2
    assert len(page2) == 2
    page1_ids = {n.id for n in page1}
    page2_ids = {n.id for n in page2}
    assert page1_ids.isdisjoint(page2_ids)


def test_repository_word_frequencies_drops_stopwords(db):
    repo = NewsRepository(db)
    db.add(News(
        title="The economy is in the news but inflation matters",
        link="https://w.example/sw-1", content_hash="sw-1", source_id=None,
    ))
    db.add(News(
        title="Inflation hits new high amid uncertainty",
        link="https://w.example/sw-2", content_hash="sw-2", source_id=None,
    ))
    db.commit()

    # Sin importar cuántas news pre-existan en la BD por tests previos, las
    # stopwords nunca deben aparecer.
    freqs = repo.word_frequencies(limit=500)
    words = {f["text"] for f in freqs}
    assert "the" not in words
    assert "is" not in words
    assert "and" not in words
    assert "of" not in words
    # Stopwords en español también.
    assert "de" not in words
    assert "la" not in words


def test_repository_word_frequencies_isolated(db):
    """Mismo test, con un dataset acotado a una keyword única: comprobamos
    que ``inflation`` aparece y que el orden por frecuencia es estable."""
    repo = NewsRepository(db)
    titles = [
        "Inflation pressure",
        "Inflation rises",
        "Inflation report",
        "Inflation impact",
        "Inflation surge",
    ]
    for i, t in enumerate(titles):
        db.add(News(
            title=t, link=f"https://w.iso/{i}",
            content_hash=f"iso-{i}", source_id=None,
        ))
    db.commit()

    freqs = repo.word_frequencies(limit=2000)
    words = {f["text"]: f["value"] for f in freqs}
    # Inflation aparece >=5 (de nuestros titulares) — sobra para ser visible
    # incluso con la limit más amplia.
    assert words.get("inflation", 0) >= 5


def test_repository_count_by_category_aggregates(db):
    repo = NewsRepository(db)
    for i, cat in enumerate(["ciencia", "ciencia", "salud", None]):
        db.add(News(
            title="x", link=f"https://cat.example/{cat}-{i}",
            category=cat, content_hash=f"hash-cat-{cat}-{i}", source_id=None,
        ))
    db.commit()

    rows = repo.count_by_category()
    by = {r["category"]: r["count"] for r in rows}
    assert by.get("ciencia") == 2
    assert by.get("salud") == 1
    # ``None`` no aparece (filtramos con isnot(None)).
    assert None not in by


# ── API: /news ──────────────────────────────────────────────────────


def test_list_news_returns_items_and_total(client, db):
    user = create_test_user(db, email="news-list@example.com")
    headers = auth_headers_for(client, user.email)
    db.add(News(
        title="List news", link="https://list.example/1",
        content_hash="list-1", source_id=None,
    ))
    db.commit()

    response = client.get("/api/v1/news", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert "total" in body
    assert body["total"] >= 1


def test_list_news_filters_by_category(client, db):
    user = create_test_user(db, email="news-filter-cat@example.com")
    headers = auth_headers_for(client, user.email)
    db.add(News(
        title="Cat news", link="https://cat.example/list",
        category="deporte", content_hash="list-cat", source_id=None,
    ))
    db.commit()

    response = client.get("/api/v1/news?category=deporte", headers=headers)
    assert response.status_code == 200
    items = response.json()["items"]
    assert all(i["category"] == "deporte" for i in items)
    assert len(items) >= 1


def test_list_news_pagination_limit(client, db):
    user = create_test_user(db, email="news-pag@example.com")
    headers = auth_headers_for(client, user.email)
    for i in range(3):
        db.add(News(
            title=f"P {i}", link=f"https://pg.example/{i}",
            content_hash=f"pag-api-{i}", source_id=None,
        ))
    db.commit()

    response = client.get("/api/v1/news?limit=2", headers=headers)
    assert response.status_code == 200
    assert len(response.json()["items"]) == 2


def test_get_news_existing_returns_200(client, db):
    user = create_test_user(db, email="news-get@example.com")
    headers = auth_headers_for(client, user.email)
    news = News(
        title="Get me", link="https://get.example/x",
        content_hash="hash-get", source_id=None,
    )
    db.add(news)
    db.commit()
    db.refresh(news)

    response = client.get(f"/api/v1/news/{news.id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["title"] == "Get me"


def test_get_news_inexistent_returns_404(client, db):
    user = create_test_user(db, email="news-get-404@example.com")
    headers = auth_headers_for(client, user.email)
    response = client.get("/api/v1/news/999999", headers=headers)
    assert response.status_code == 404


def test_news_stats_global(client, db):
    user = create_test_user(db, email="news-stats@example.com")
    headers = auth_headers_for(client, user.email)
    db.add(News(
        title="Stats", link="https://stats.example/x",
        category="economia", content_hash="hash-stats", source_id=None,
    ))
    db.commit()

    response = client.get("/api/v1/news/stats", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert "total_news" in body
    assert "by_category" in body


def test_news_wordcloud_global(client, db):
    user = create_test_user(db, email="news-wc@example.com")
    headers = auth_headers_for(client, user.email)
    db.add(News(
        title="Inflation rising globally", link="https://wc.example/x",
        content_hash="hash-wc", source_id=None,
    ))
    db.commit()

    response = client.get("/api/v1/news/wordcloud", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)


def test_news_me_stats_with_no_notifications_returns_zero(client, db):
    user = create_test_user(db, email="news-me-stats@example.com")
    headers = auth_headers_for(client, user.email)
    response = client.get("/api/v1/news/me/stats", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total_news"] == 0


def test_news_me_wordcloud_returns_empty_for_user_without_notifications(client, db):
    user = create_test_user(db, email="news-me-wc@example.com")
    headers = auth_headers_for(client, user.email)
    response = client.get("/api/v1/news/me/wordcloud", headers=headers)
    assert response.status_code == 200
    assert response.json() == []


def test_news_me_stats_with_notifications(client, db):
    """User stats deben venir SOLO de las news con notification asociada al user."""
    from app.modules.alerts.schemas import AlertCreateInternal
    from app.modules.alerts.service import AlertService
    from app.modules.alerts.repository import AlertRepository

    user = create_test_user(db, email="news-me-with-notif@example.com")
    # Crear una news + una alerta + una notification para ese user.
    news = News(
        title="Politica titular", link="https://mes.example/n",
        category="politica", content_hash="me-stats-1", source_id=None,
    )
    db.add(news)
    db.commit()
    db.refresh(news)

    alert_payload = AlertCreateInternal(
        name="Mine", descriptors=["a", "b", "c"], categories=[],
        rss_channels_ids=[], information_sources_ids=[],
        cron_expression="*/5 * * * *",
    )
    alert = AlertService(AlertRepository(db)).create_alert(alert_payload, user.id)

    notif_repo = NotificationRepository(db)
    notif_repo.create(
        title="t", message="m", user_id=user.id, alert_id=alert.id,
        news_id=news.id, timestamp=datetime.now(timezone.utc), metrics=[],
    )

    headers = auth_headers_for(client, user.email)
    response = client.get("/api/v1/news/me/stats", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total_news"] >= 1
    cats = {row["category"] for row in body["by_category"]}
    assert "politica" in cats


def test_news_unauthenticated_returns_401(client, db):
    response = client.get("/api/v1/news")
    assert response.status_code == 401
