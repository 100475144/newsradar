"""Tests del módulo ``notifications``.

Cubre:
* ``notifications/service.py`` — flujo CRUD anidado (list/get/update/delete),
  metrics normalization, mark_as_read/unread, get_for_user 404,
  build_default_metrics con/sin source_name.
* ``notifications/api.py`` — endpoints anidados oficiales
  (``/users/{uid}/alerts/{aid}/notifications``) y endpoints "me"
  (``/users/me/notifications/...``) incluidos los PATCH read/unread.
* ``notifications/repository.py`` — idempotencia por
  ``(user_id, alert_id, news_id)`` (delivery key) y filtros por user/alert.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.modules.alerts.repository import AlertRepository
from app.modules.alerts.schemas import AlertCreateInternal
from app.modules.alerts.service import AlertService
from app.modules.notifications.repository import NotificationRepository
from app.modules.notifications.service import (
    NotificationService,
    _normalize_metrics,
    build_default_metrics,
)
from app.modules.notifications.schemas import Metric
from app.tests.helpers import auth_headers_for, create_test_user


VALID_ALERT_PAYLOAD = {
    "name": "Notif Alert",
    "descriptors": ["ai", "ml", "neural networks"],
    "categories": [{"code": "13000000", "label": "Ciencia y tecnología"}],
    "rss_channels_ids": [],
    "information_sources_ids": [],
    "cron_expression": "*/5 * * * *",
    "keyword": "ai",
    "notify_in_app": True,
    "notify_email": False,
}


def _make_user_with_alert(client, db, email: str):
    user = create_test_user(db, email=email)
    headers = auth_headers_for(client, user.email)
    response = client.post(
        "/api/v1/users/me/alerts", json=VALID_ALERT_PAYLOAD, headers=headers,
    )
    assert response.status_code == 201, response.text
    return user, headers, response.json()["id"]


# ── _normalize_metrics ───────────────────────────────────────────────


def test_normalize_metrics_filters_and_casts():
    raw = [
        {"name": "good", "value": "3.5"},
        {"name": "  with_spaces  ", "value": 1},
        {"name": "", "value": 5},          # nombre vacío → descartado
        {"name": "missing_value"},         # value None → descartado
        {"name": "nonnumeric", "value": "abc"},  # no convertible → descartado
        "not a dict",
        None,
    ]
    out = _normalize_metrics(raw)
    assert {m["name"] for m in out} == {"good", "with_spaces"}
    assert all(isinstance(m["value"], float) for m in out)


def test_normalize_metrics_accepts_pydantic_models():
    out = _normalize_metrics([Metric(name="latency", value=12.5)])
    assert out == [{"name": "latency", "value": 12.5}]


def test_normalize_metrics_empty_returns_empty():
    assert _normalize_metrics(None) == []
    assert _normalize_metrics([]) == []


# ── build_default_metrics ────────────────────────────────────────────


class _FakeNews:
    def __init__(self, title="t", summary="s"):
        self.title = title
        self.summary = summary


def test_build_default_metrics_with_known_source():
    metrics = build_default_metrics(_FakeNews("hello", "world"), "El País")
    names = {m["name"]: m["value"] for m in metrics}
    assert names["title_length_chars"] == 5.0
    assert names["summary_length_chars"] == 5.0
    assert names["has_known_source"] == 1.0


def test_build_default_metrics_without_source():
    metrics = build_default_metrics(_FakeNews(), None)
    names = {m["name"]: m["value"] for m in metrics}
    assert names["has_known_source"] == 0.0


# ── Endpoints anidados oficiales /users/{u}/alerts/{a}/notifications ─


def test_create_notification_anidado_201(client, db):
    user, headers, alert_id = _make_user_with_alert(client, db, "n-create@example.com")

    response = client.post(
        f"/api/v1/users/{user.id}/alerts/{alert_id}/notifications",
        json={
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": [{"name": "score", "value": 0.9}],
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["alert_id"] == alert_id
    assert body["metrics"] == [{"name": "score", "value": 0.9}]


def test_create_notification_missing_timestamp_returns_422(client, db):
    user, headers, alert_id = _make_user_with_alert(client, db, "n-no-ts@example.com")

    response = client.post(
        f"/api/v1/users/{user.id}/alerts/{alert_id}/notifications",
        json={"metrics": []},
        headers=headers,
    )
    assert response.status_code == 422


def test_list_notifications_returns_only_for_that_alert(client, db):
    user, headers, alert_id = _make_user_with_alert(client, db, "n-list@example.com")
    ts = datetime.now(timezone.utc).isoformat()
    for _ in range(3):
        r = client.post(
            f"/api/v1/users/{user.id}/alerts/{alert_id}/notifications",
            json={"timestamp": ts, "metrics": []},
            headers=headers,
        )
        assert r.status_code == 201

    response = client.get(
        f"/api/v1/users/{user.id}/alerts/{alert_id}/notifications",
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    # >= 3: pueden existir además notificaciones generadas por el backfill
    # del matching engine sobre news pre-existentes en la BD de tests.
    assert len(body) >= 3
    assert all(n["alert_id"] == alert_id for n in body)
    # Las 3 que acabamos de crear manualmente tienen metrics=[].
    manual = [n for n in body if n["metrics"] == []]
    assert len(manual) >= 3


def test_get_notification_returns_200(client, db):
    user, headers, alert_id = _make_user_with_alert(client, db, "n-get@example.com")
    ts = datetime.now(timezone.utc).isoformat()
    r = client.post(
        f"/api/v1/users/{user.id}/alerts/{alert_id}/notifications",
        json={"timestamp": ts, "metrics": []},
        headers=headers,
    )
    notif_id = r.json()["id"]

    response = client.get(
        f"/api/v1/users/{user.id}/alerts/{alert_id}/notifications/{notif_id}",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["id"] == notif_id


def test_get_notification_inexistent_returns_404(client, db):
    user, headers, alert_id = _make_user_with_alert(client, db, "n-get-404@example.com")
    response = client.get(
        f"/api/v1/users/{user.id}/alerts/{alert_id}/notifications/999999",
        headers=headers,
    )
    assert response.status_code == 404


def test_update_notification_changes_metrics(client, db):
    user, headers, alert_id = _make_user_with_alert(client, db, "n-upd@example.com")
    ts = datetime.now(timezone.utc).isoformat()
    r = client.post(
        f"/api/v1/users/{user.id}/alerts/{alert_id}/notifications",
        json={"timestamp": ts, "metrics": [{"name": "a", "value": 1.0}]},
        headers=headers,
    )
    notif_id = r.json()["id"]

    response = client.put(
        f"/api/v1/users/{user.id}/alerts/{alert_id}/notifications/{notif_id}",
        json={"metrics": [{"name": "b", "value": 2.0}]},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["metrics"] == [{"name": "b", "value": 2.0}]


def test_update_notification_empty_body_noop(client, db):
    user, headers, alert_id = _make_user_with_alert(client, db, "n-upd-noop@example.com")
    ts = datetime.now(timezone.utc).isoformat()
    r = client.post(
        f"/api/v1/users/{user.id}/alerts/{alert_id}/notifications",
        json={"timestamp": ts, "metrics": []},
        headers=headers,
    )
    notif_id = r.json()["id"]
    response = client.put(
        f"/api/v1/users/{user.id}/alerts/{alert_id}/notifications/{notif_id}",
        json={},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["id"] == notif_id


def test_delete_notification_returns_204(client, db):
    user, headers, alert_id = _make_user_with_alert(client, db, "n-del@example.com")
    ts = datetime.now(timezone.utc).isoformat()
    r = client.post(
        f"/api/v1/users/{user.id}/alerts/{alert_id}/notifications",
        json={"timestamp": ts, "metrics": []},
        headers=headers,
    )
    notif_id = r.json()["id"]

    response = client.delete(
        f"/api/v1/users/{user.id}/alerts/{alert_id}/notifications/{notif_id}",
        headers=headers,
    )
    assert response.status_code == 204


def test_other_user_cannot_access_notifications_403(client, db):
    user_a, headers_a, alert_id = _make_user_with_alert(client, db, "n-acl-a@example.com")
    user_b = create_test_user(db, email="n-acl-b@example.com")
    headers_b = auth_headers_for(client, user_b.email)

    response = client.get(
        f"/api/v1/users/{user_a.id}/alerts/{alert_id}/notifications",
        headers=headers_b,
    )
    assert response.status_code == 403


def test_anidado_nonexistent_alert_returns_404(client, db):
    user = create_test_user(db, email="n-noalert@example.com")
    headers = auth_headers_for(client, user.email)
    response = client.get(
        f"/api/v1/users/{user.id}/alerts/999999/notifications",
        headers=headers,
    )
    assert response.status_code == 404


# ── Endpoints "me" para la UI ───────────────────────────────────────


def _seed_notification_via_repository(db, user_id: int, alert_id: int) -> int:
    repo = NotificationRepository(db)
    n = repo.create(
        title="Test",
        message="msg",
        user_id=user_id,
        alert_id=alert_id,
        news_id=None,
        timestamp=datetime.now(timezone.utc),
        metrics=[{"name": "x", "value": 1.0}],
    )
    return n.id


def test_list_my_notifications_returns_inbox(client, db):
    user, _, alert_id = _make_user_with_alert(client, db, "n-me-list@example.com")
    _seed_notification_via_repository(db, user.id, alert_id)

    headers = auth_headers_for(client, user.email)
    response = client.get("/api/v1/users/me/notifications", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body) >= 1
    assert body[0]["user_id"] == user.id


def test_get_my_notification_details_returns_enriched_schema(client, db):
    user, _, alert_id = _make_user_with_alert(client, db, "n-me-det@example.com")
    notif_id = _seed_notification_via_repository(db, user.id, alert_id)

    headers = auth_headers_for(client, user.email)
    response = client.get(
        f"/api/v1/users/me/notifications/{notif_id}/details", headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == notif_id
    assert body["title"] == "Test"
    assert body["is_read"] is False


def test_mark_as_read_then_unread(client, db):
    user, _, alert_id = _make_user_with_alert(client, db, "n-me-read@example.com")
    notif_id = _seed_notification_via_repository(db, user.id, alert_id)

    headers = auth_headers_for(client, user.email)
    r = client.patch(
        f"/api/v1/users/me/notifications/{notif_id}/read", headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["is_read"] is True

    r = client.patch(
        f"/api/v1/users/me/notifications/{notif_id}/unread", headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["is_read"] is False


def test_delete_my_notification_returns_204(client, db):
    user, _, alert_id = _make_user_with_alert(client, db, "n-me-del@example.com")
    notif_id = _seed_notification_via_repository(db, user.id, alert_id)

    headers = auth_headers_for(client, user.email)
    r = client.delete(
        f"/api/v1/users/me/notifications/{notif_id}", headers=headers,
    )
    assert r.status_code == 204


def test_my_notification_not_found_returns_404(client, db):
    user = create_test_user(db, email="n-me-404@example.com")
    headers = auth_headers_for(client, user.email)
    r = client.get(
        "/api/v1/users/me/notifications/999999/details", headers=headers,
    )
    assert r.status_code == 404


def test_mark_other_users_notification_returns_404(client, db):
    """Una notificación de otro usuario no aparece en mi bandeja → 404 (no 403)."""
    user_a, _, alert_id_a = _make_user_with_alert(client, db, "n-acl-a-me@example.com")
    notif_id = _seed_notification_via_repository(db, user_a.id, alert_id_a)

    user_b = create_test_user(db, email="n-acl-b-me@example.com")
    headers_b = auth_headers_for(client, user_b.email)
    r = client.patch(
        f"/api/v1/users/me/notifications/{notif_id}/read", headers=headers_b,
    )
    assert r.status_code == 404


# ── Repository idempotencia por delivery key ────────────────────────


def test_repository_create_is_idempotent_on_delivery_key(db):
    user = create_test_user(db, email="repo-idem@example.com")
    alert_repo = AlertRepository(db)
    alert_service = AlertService(alert_repo)
    payload = AlertCreateInternal(**{**VALID_ALERT_PAYLOAD, "name": "Idem-Alert"})
    alert = alert_service.create_alert(payload, user.id)

    # Crear News asociada para activar el delivery key.
    from app.modules.news.models import News

    news = News(
        title="N", link="https://example.com/n", summary="s",
        source_id=None,
    )
    db.add(news)
    db.commit()
    db.refresh(news)

    notif_repo = NotificationRepository(db)
    n1 = notif_repo.create(
        title="t1", message="m1", user_id=user.id, alert_id=alert.id,
        news_id=news.id, timestamp=datetime.now(timezone.utc), metrics=[],
    )
    # Segundo intento con la misma (user, alert, news) debe devolver la misma
    # fila, NO crear duplicado.
    n2 = notif_repo.create(
        title="t2", message="m2", user_id=user.id, alert_id=alert.id,
        news_id=news.id, timestamp=datetime.now(timezone.utc), metrics=[],
    )
    assert n1.id == n2.id

    rows = notif_repo.list_for_alert(alert.id)
    assert len([r for r in rows if r.news_id == news.id]) == 1
