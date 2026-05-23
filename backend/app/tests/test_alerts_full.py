"""Tests adicionales para el módulo ``alerts`` con foco en cobertura.

Cubre rutas y reglas no cubiertas por ``test_alerts_per_user.py`` y
``test_alert_email_notification.py``:

* ``alerts/recommender.py`` — unit tests directos de
  ``suggest_expanded_keywords`` (exact match, partial match, fallback,
  min 3, max 10, dedup, empty).
* ``alerts/schemas.py`` — validación de cron (válido + inválido),
  limpieza de descriptors, ``AlertUpdate`` con campos opcionales.
* ``alerts/service.py`` — duplicado case-insensitive, >1 categoría,
  código IPTC inválido, label mismatch, autorelleno de descriptors,
  activate/deactivate, get_alert 404.
* ``alerts/api.py`` — rutas auxiliares (``/alerts/categories``,
  ``/alerts/suggestions/{kw}``, ``/alerts/me/stats``), endpoint
  anidado oficial con permisos (admin ve todo, gestor sólo lo suyo),
  alias ``/users/me/alerts``.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.modules.alerts.recommender import suggest_expanded_keywords
from app.modules.alerts.repository import AlertRepository
from app.modules.alerts.schemas import (
    AlertBase,
    AlertCategoryItem,
    AlertCreateInternal,
    AlertUpdate,
)
from app.modules.alerts.service import (
    AlertService,
    _normalize_categories,
    _normalize_id_list,
)
from app.tests.helpers import auth_headers_for, create_test_user


VALID_PAYLOAD = {
    "name": "Cobertura Alert",
    "descriptors": ["ai", "machine learning", "neural networks"],
    "categories": [{"code": "13000000", "label": "Ciencia y tecnología"}],
    "rss_channels_ids": [],
    "information_sources_ids": [],
    "cron_expression": "*/5 * * * *",
    "keyword": "ai",
    "notify_in_app": True,
    "notify_email": False,
}


# ── recommender.suggest_expanded_keywords ────────────────────────────


def test_recommender_exact_match_returns_related_terms():
    result = suggest_expanded_keywords("bitcoin")
    assert len(result) >= 3
    assert len(result) <= 10
    # Some related term from the dictionary should appear.
    assert any(term in result for term in ["btc", "cryptocurrency", "blockchain"])


def test_recommender_case_insensitive():
    lower = suggest_expanded_keywords("bitcoin")
    upper = suggest_expanded_keywords("BITCOIN")
    assert lower == upper


def test_recommender_partial_match_substring():
    # "deep learning" no es key exacta pero "machine learning" contiene piezas
    # — probamos un caso de partial match.
    result = suggest_expanded_keywords("artificial intelligence is here")
    assert len(result) >= 3


def test_recommender_unknown_keyword_falls_back_to_generic_suffixes():
    result = suggest_expanded_keywords("xyzzy-frob")
    assert len(result) >= 3
    # El fallback usa la propia keyword con sufijos genéricos.
    base = "xyzzy frob"
    assert any(base in term for term in result)


def test_recommender_returns_max_10():
    # Una keyword con muchos términos relacionados debería seguir <= 10.
    result = suggest_expanded_keywords("ai")
    assert len(result) <= 10


def test_recommender_empty_keyword_raises():
    with pytest.raises(ValueError):
        suggest_expanded_keywords("")
    with pytest.raises(ValueError):
        suggest_expanded_keywords("   ")


def test_recommender_deduplicates_and_strips():
    # No podemos forzar duplicados desde fuera, pero comprobamos que el
    # output no contiene la propia keyword.
    result = suggest_expanded_keywords("bitcoin")
    assert "bitcoin" not in result


# ── schemas: validación de cron y descriptors ────────────────────────


def test_schema_cron_invalid_raises():
    with pytest.raises(ValidationError):
        AlertBase(
            name="x",
            descriptors=["a", "b", "c"],
            categories=[],
            rss_channels_ids=[],
            information_sources_ids=[],
            cron_expression="not a cron",
        )


def test_schema_cron_valid_passes():
    obj = AlertBase(
        name="x",
        descriptors=["a", "b", "c"],
        categories=[],
        rss_channels_ids=[],
        information_sources_ids=[],
        cron_expression="0 9 * * 1-5",
    )
    assert obj.cron_expression == "0 9 * * 1-5"


def test_schema_descriptors_dedup_and_strip():
    obj = AlertBase(
        name="x",
        descriptors=["  ai  ", "AI", "", "machine learning", "machine learning"],
        categories=[],
        rss_channels_ids=[],
        information_sources_ids=[],
        cron_expression="*/5 * * * *",
    )
    # "ai" se mantiene una sola vez (case-insensitive dedup).
    assert len(obj.descriptors) == 2
    assert "ai" in [d.lower() for d in obj.descriptors]
    assert "machine learning" in [d.lower() for d in obj.descriptors]


def test_schema_alert_update_cron_optional_none():
    upd = AlertUpdate(cron_expression=None)
    assert upd.cron_expression is None


def test_schema_alert_update_cron_invalid_raises():
    with pytest.raises(ValidationError):
        AlertUpdate(cron_expression="invalid")


def test_schema_alert_update_descriptors_dedup():
    upd = AlertUpdate(descriptors=["AI", "ai", "ml"])
    assert len(upd.descriptors) == 2


def test_schema_alert_update_descriptors_none():
    upd = AlertUpdate(descriptors=None)
    assert upd.descriptors is None


# ── service helpers: _normalize_categories / _normalize_id_list ──────


def test_normalize_categories_accepts_pydantic_models():
    items = [AlertCategoryItem(code="13000000", label="Ciencia y tecnología")]
    result = _normalize_categories(items)
    assert result == [{"code": "13000000", "label": "Ciencia y tecnología"}]


def test_normalize_categories_dedups_by_code():
    items = [
        {"code": "13000000", "label": "Ciencia y tecnología"},
        {"code": "13000000", "label": "Ciencia y tecnología"},
    ]
    result = _normalize_categories(items)
    assert len(result) == 1


def test_normalize_categories_rejects_invalid_code():
    with pytest.raises(HTTPException) as excinfo:
        _normalize_categories([{"code": "99999999", "label": "Whatever"}])
    assert excinfo.value.status_code == 400


def test_normalize_categories_rejects_label_mismatch():
    with pytest.raises(HTTPException) as excinfo:
        _normalize_categories(
            [{"code": "13000000", "label": "Wrong label"}],
        )
    assert excinfo.value.status_code == 400


def test_normalize_categories_skips_invalid_entries():
    # Entradas que no son dict ni tienen model_dump se ignoran.
    result = _normalize_categories([None, 42, "string"])
    assert result == []


def test_normalize_categories_skips_empty_code():
    result = _normalize_categories([{"code": "  ", "label": "foo"}])
    assert result == []


def test_normalize_id_list_dedups_and_strips():
    result = _normalize_id_list(["a", " a ", "b", "", "  ", "c", "c"])
    assert result == ["a", "b", "c"]


def test_normalize_id_list_handles_none():
    assert _normalize_id_list([]) == []


# ── service: AlertService a través de la API ─────────────────────────


def test_create_alert_duplicate_name_case_insensitive_returns_409(client, db):
    user = create_test_user(db, email="alert-dup@example.com")
    headers = auth_headers_for(client, user.email)

    response = client.post("/api/v1/users/me/alerts", json=VALID_PAYLOAD, headers=headers)
    assert response.status_code == 201

    dup = {**VALID_PAYLOAD, "name": "COBERTURA ALERT"}
    response = client.post("/api/v1/users/me/alerts", json=dup, headers=headers)
    assert response.status_code == 409


def test_create_alert_more_than_one_category_returns_400(client, db):
    user = create_test_user(db, email="alert-multicat@example.com")
    headers = auth_headers_for(client, user.email)

    payload = {
        **VALID_PAYLOAD,
        "categories": [
            {"code": "13000000", "label": "Ciencia y tecnología"},
            {"code": "11000000", "label": "Política"},
        ],
    }
    response = client.post("/api/v1/users/me/alerts", json=payload, headers=headers)
    assert response.status_code == 400


def test_create_alert_invalid_category_code_returns_400(client, db):
    user = create_test_user(db, email="alert-badcat@example.com")
    headers = auth_headers_for(client, user.email)

    payload = {
        **VALID_PAYLOAD,
        "categories": [{"code": "99999999", "label": "Whatever"}],
    }
    response = client.post("/api/v1/users/me/alerts", json=payload, headers=headers)
    assert response.status_code == 400


def test_create_alert_label_mismatch_returns_400(client, db):
    user = create_test_user(db, email="alert-mismatch@example.com")
    headers = auth_headers_for(client, user.email)

    payload = {
        **VALID_PAYLOAD,
        "categories": [{"code": "13000000", "label": "Wrong Label"}],
    }
    response = client.post("/api/v1/users/me/alerts", json=payload, headers=headers)
    assert response.status_code == 400


def test_create_alert_few_descriptors_autofills_to_three(client, db):
    user = create_test_user(db, email="alert-autofill@example.com")
    headers = auth_headers_for(client, user.email)

    payload = {**VALID_PAYLOAD, "descriptors": ["ai"], "keyword": "ai"}
    response = client.post("/api/v1/users/me/alerts", json=payload, headers=headers)
    assert response.status_code == 201
    body = response.json()
    assert len(body["descriptors"]) >= 3


def test_create_alert_empty_descriptors_autofills_with_keyword(client, db):
    user = create_test_user(db, email="alert-autofill-2@example.com")
    headers = auth_headers_for(client, user.email)

    payload = {**VALID_PAYLOAD, "descriptors": [], "keyword": "bitcoin"}
    response = client.post("/api/v1/users/me/alerts", json=payload, headers=headers)
    assert response.status_code == 201
    body = response.json()
    assert len(body["descriptors"]) >= 3


def test_create_alert_for_inexistent_user_returns_404(client, db):
    admin = create_test_user(db, email="alert-admin-404@example.com", role="admin")
    headers = auth_headers_for(client, admin.email)

    response = client.post(
        "/api/v1/users/999999/alerts", json=VALID_PAYLOAD, headers=headers,
    )
    assert response.status_code == 404


# ── service: get/update/delete/activate/deactivate ───────────────────


def _create_alert(client, headers, name: str = "Cov-Alert") -> int:
    payload = {**VALID_PAYLOAD, "name": name}
    response = client.post("/api/v1/users/me/alerts", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_get_alert_inexistent_returns_404(client, db):
    user = create_test_user(db, email="alert-get-404@example.com")
    headers = auth_headers_for(client, user.email)

    response = client.get(
        f"/api/v1/users/{user.id}/alerts/999999", headers=headers,
    )
    assert response.status_code == 404


def test_update_alert_changes_name(client, db):
    user = create_test_user(db, email="alert-upd@example.com")
    headers = auth_headers_for(client, user.email)
    alert_id = _create_alert(client, headers)

    response = client.put(
        f"/api/v1/users/{user.id}/alerts/{alert_id}",
        json={"name": "Renamed"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Renamed"


def test_update_alert_changes_categories(client, db):
    user = create_test_user(db, email="alert-upd-cat@example.com")
    headers = auth_headers_for(client, user.email)
    alert_id = _create_alert(client, headers, name="Cat-Alert")

    response = client.put(
        f"/api/v1/users/{user.id}/alerts/{alert_id}",
        json={
            "categories": [{"code": "11000000", "label": "Política"}],
        },
        headers=headers,
    )
    assert response.status_code == 200
    cats = response.json()["categories"]
    assert cats == [{"code": "11000000", "label": "Política"}]


def test_update_alert_inexistent_returns_404(client, db):
    user = create_test_user(db, email="alert-upd-404@example.com")
    headers = auth_headers_for(client, user.email)

    response = client.put(
        f"/api/v1/users/{user.id}/alerts/999999",
        json={"name": "x"},
        headers=headers,
    )
    assert response.status_code == 404


def test_delete_alert_returns_204(client, db):
    user = create_test_user(db, email="alert-del@example.com")
    headers = auth_headers_for(client, user.email)
    alert_id = _create_alert(client, headers, name="Del-Alert")

    response = client.delete(
        f"/api/v1/users/{user.id}/alerts/{alert_id}", headers=headers,
    )
    assert response.status_code == 204


def test_delete_alert_inexistent_returns_404(client, db):
    user = create_test_user(db, email="alert-del-404@example.com")
    headers = auth_headers_for(client, user.email)

    response = client.delete(
        f"/api/v1/users/{user.id}/alerts/999999", headers=headers,
    )
    assert response.status_code == 404


def test_activate_then_deactivate_alert(client, db):
    user = create_test_user(db, email="alert-act@example.com")
    headers = auth_headers_for(client, user.email)
    alert_id = _create_alert(client, headers, name="Act-Alert")

    deact = client.patch(
        f"/api/v1/users/{user.id}/alerts/{alert_id}/deactivate", headers=headers,
    )
    assert deact.status_code == 200
    assert deact.json()["is_active"] is False

    act = client.patch(
        f"/api/v1/users/{user.id}/alerts/{alert_id}/activate", headers=headers,
    )
    assert act.status_code == 200
    assert act.json()["is_active"] is True


# ── endpoints anidados: permisos ─────────────────────────────────────


def test_list_alerts_admin_can_see_other_users(client, db):
    admin = create_test_user(db, email="alert-admin-list@example.com", role="admin")
    other = create_test_user(db, email="alert-other-list@example.com")
    headers_other = auth_headers_for(client, other.email)
    _create_alert(client, headers_other, name="Other's Alert")

    headers_admin = auth_headers_for(client, admin.email)
    response = client.get(
        f"/api/v1/users/{other.id}/alerts", headers=headers_admin,
    )
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_list_alerts_user_cannot_see_other_users(client, db):
    user_a = create_test_user(db, email="alert-list-a@example.com")
    user_b = create_test_user(db, email="alert-list-b@example.com")
    headers_a = auth_headers_for(client, user_a.email)

    response = client.get(
        f"/api/v1/users/{user_b.id}/alerts", headers=headers_a,
    )
    assert response.status_code == 403


# ── helpers_router: /alerts/categories, /alerts/suggestions, stats ──


def test_list_iptc_categories_endpoint_returns_17(client, db):
    user = create_test_user(db, email="alert-cats@example.com")
    headers = auth_headers_for(client, user.email)

    response = client.get("/api/v1/alerts/categories", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 17
    assert all("code" in c and "label" in c for c in body)


def test_get_keyword_suggestions_endpoint(client, db):
    user = create_test_user(db, email="alert-sugg@example.com")
    headers = auth_headers_for(client, user.email)

    response = client.get("/api/v1/alerts/suggestions/bitcoin", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["keyword"] == "bitcoin"
    assert body["count"] == len(body["suggestions"])
    assert body["count"] >= 3


def test_my_alerts_stats_empty(client, db):
    user = create_test_user(db, email="alert-stats-empty@example.com")
    headers = auth_headers_for(client, user.email)

    response = client.get("/api/v1/alerts/me/stats", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total_alerts"] == 0
    assert body["by_category"] == []


def test_my_alerts_stats_aggregates_by_category(client, db):
    user = create_test_user(db, email="alert-stats-agg@example.com")
    headers = auth_headers_for(client, user.email)

    _create_alert(client, headers, name="Stats-1")
    # Crear otra con categoría distinta para tener dos buckets.
    payload = {
        **VALID_PAYLOAD,
        "name": "Stats-2",
        "categories": [{"code": "11000000", "label": "Política"}],
    }
    response = client.post("/api/v1/users/me/alerts", json=payload, headers=headers)
    assert response.status_code == 201

    response = client.get("/api/v1/alerts/me/stats", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total_alerts"] == 2
    codes = {row["category"] for row in body["by_category"]}
    assert "13000000" in codes
    assert "11000000" in codes


# ── repository: list_active y count_for_user ─────────────────────────


def test_repository_list_active_filters_inactive(db):
    user = create_test_user(db, email="repo-active@example.com")
    repo = AlertRepository(db)
    service = AlertService(repo)

    payload = AlertCreateInternal(**{**VALID_PAYLOAD, "name": "Repo-Active"})
    alert = service.create_alert(payload, user.id)
    assert alert.is_active is True

    service.deactivate_alert(alert.id, user.id)
    actives = repo.list_active()
    assert all(a.is_active for a in actives)
    assert alert.id not in {a.id for a in actives}


def test_service_get_alert_for_wrong_user_returns_404(db):
    user_a = create_test_user(db, email="svc-a@example.com")
    user_b = create_test_user(db, email="svc-b@example.com")
    repo = AlertRepository(db)
    service = AlertService(repo)

    payload = AlertCreateInternal(**{**VALID_PAYLOAD, "name": "Owned-by-A"})
    alert = service.create_alert(payload, user_a.id)

    with pytest.raises(HTTPException) as excinfo:
        service.get_alert(alert.id, user_b.id)
    assert excinfo.value.status_code == 404
