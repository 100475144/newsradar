"""Tests de alertas per-user con el schema oficial (T6.4 + CAMBIO #2)."""

from __future__ import annotations

from app.tests.helpers import auth_headers_for, create_test_user


VALID_PAYLOAD = {
    "name": "Test Alert",
    "descriptors": ["ai", "machine learning", "neural networks"],
    "categories": [{"code": "science_technology", "label": "Science and Technology"}],
    "rss_channels_ids": [],
    "information_sources_ids": [],
    "cron_expression": "*/5 * * * *",
    "keyword": "ai",
    "notify_in_app": True,
    "notify_email": False,
}


def test_create_alert_returns_official_schema(client, db):
    user = create_test_user(db, email="alert-create@example.com")
    headers = auth_headers_for(client, user.email)

    response = client.post(
        "/api/v1/users/me/alerts",
        json=VALID_PAYLOAD,
        headers=headers,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    # Schema oficial: name, descriptors, categories[], rss_channels_ids[],
    # information_sources_ids[], cron_expression, id, user_id.
    assert body["name"] == "Test Alert"
    assert body["descriptors"] == ["ai", "machine learning", "neural networks"]
    assert body["categories"] == [
        {"code": "science_technology", "label": "Science and Technology"}
    ]
    assert body["rss_channels_ids"] == []
    assert body["information_sources_ids"] == []
    assert body["user_id"] == user.id


def test_alerts_are_per_user(client, db):
    user_a = create_test_user(db, email="alert-a@example.com")
    user_b = create_test_user(db, email="alert-b@example.com")

    headers_a = auth_headers_for(client, user_a.email)
    headers_b = auth_headers_for(client, user_b.email)

    # A crea una alerta.
    response = client.post(
        "/api/v1/users/me/alerts",
        json=VALID_PAYLOAD,
        headers=headers_a,
    )
    assert response.status_code == 201

    # A la ve.
    response = client.get("/api/v1/users/me/alerts", headers=headers_a)
    assert response.status_code == 200
    assert len(response.json()) == 1

    # B NO la ve (per-user — CAMBIO #2).
    response = client.get("/api/v1/users/me/alerts", headers=headers_b)
    assert response.status_code == 200
    assert response.json() == []


def test_user_cannot_access_other_users_alerts_explicitly(client, db):
    user_a = create_test_user(db, email="alert-c@example.com")
    user_b = create_test_user(db, email="alert-d@example.com")

    headers_a = auth_headers_for(client, user_a.email)
    headers_b = auth_headers_for(client, user_b.email)

    response = client.post(
        "/api/v1/users/me/alerts", json=VALID_PAYLOAD, headers=headers_a,
    )
    alert_id = response.json()["id"]

    # B intenta acceder a una alerta de A vía el endpoint anidado oficial.
    response = client.get(
        f"/api/v1/users/{user_a.id}/alerts/{alert_id}",
        headers=headers_b,
    )
    assert response.status_code == 403


def test_alert_validation_rejects_invalid_cron(client, db):
    user = create_test_user(db, email="alert-cron@example.com")
    headers = auth_headers_for(client, user.email)

    bad_payload = {**VALID_PAYLOAD, "cron_expression": "this is not cron"}
    response = client.post(
        "/api/v1/users/me/alerts", json=bad_payload, headers=headers,
    )
    assert response.status_code == 422


def test_alert_max_limit_per_gestor(client, db):
    """Checklist #3: máx 20 alertas por gestor."""
    user = create_test_user(db, email="alert-limit@example.com")
    headers = auth_headers_for(client, user.email)

    for i in range(20):
        payload = {**VALID_PAYLOAD, "name": f"Alert #{i}"}
        response = client.post(
            "/api/v1/users/me/alerts", json=payload, headers=headers,
        )
        assert response.status_code == 201

    # La alerta 21 debe rechazarse.
    payload = {**VALID_PAYLOAD, "name": "Alert too many"}
    response = client.post(
        "/api/v1/users/me/alerts", json=payload, headers=headers,
    )
    assert response.status_code == 400
    assert "20" in response.json()["detail"]
