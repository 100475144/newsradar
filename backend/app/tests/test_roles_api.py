"""Tests CRUD oficiales del recurso ``Role`` (``/api/v1/roles``).

Cubre ``backend/app/modules/auth/roles_api.py``.

Reglas testadas:
* ``GET /roles``: cualquier autenticado.
* ``POST /roles``: cualquier autenticado. Valida nombre no vacío, longitud
  máxima 90, caracteres permitidos, duplicado case-insensitive.
* ``GET /roles/{id}``: 404 si no existe.
* ``PUT /roles/{id}``: 409 si el nuevo nombre choca con otro rol.
* ``DELETE /roles/{id}``: 409 si el rol está asignado a usuarios.
"""

from __future__ import annotations

from app.tests.helpers import (
    auth_headers_for,
    create_test_user,
    ensure_canonical_roles,
)


# ── GET /roles ───────────────────────────────────────────────────────


def test_list_roles_returns_200_with_canonical(client, db):
    ensure_canonical_roles(db)
    user = create_test_user(db, email="rl@example.com")
    headers = auth_headers_for(client, user.email)
    response = client.get("/api/v1/roles", headers=headers)
    assert response.status_code == 200
    names = {r["name"] for r in response.json()}
    assert "admin" in names
    assert "gestor" in names


def test_list_roles_unauthenticated_returns_401(client, db):
    response = client.get("/api/v1/roles")
    assert response.status_code == 401


# ── POST /roles ──────────────────────────────────────────────────────


def test_create_role_valid_returns_201(client, db):
    user = create_test_user(db, email="rc-valid@example.com")
    headers = auth_headers_for(client, user.email)
    response = client.post(
        "/api/v1/roles",
        json={"name": "moderator"},
        headers=headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "moderator"
    assert isinstance(body["id"], int)


def test_create_role_whitespace_name_returns_400(client, db):
    user = create_test_user(db, email="rc-blank@example.com")
    headers = auth_headers_for(client, user.email)
    response = client.post(
        "/api/v1/roles",
        json={"name": "   "},
        headers=headers,
    )
    # Pydantic puede rechazar con 422 (min_length=1 fallaría sólo si vacío
    # literal) o el endpoint con 400 tras strip. Aceptamos ambos.
    assert response.status_code in {400, 422}


def test_create_role_long_name_returns_400_or_422(client, db):
    user = create_test_user(db, email="rc-long@example.com")
    headers = auth_headers_for(client, user.email)
    response = client.post(
        "/api/v1/roles",
        json={"name": "x" * 200},
        headers=headers,
    )
    assert response.status_code in {400, 422}


def test_create_role_invalid_chars_returns_400(client, db):
    user = create_test_user(db, email="rc-ic@example.com")
    headers = auth_headers_for(client, user.email)
    response = client.post(
        "/api/v1/roles",
        json={"name": "bad@chars!"},
        headers=headers,
    )
    assert response.status_code == 400


def test_create_role_with_allowed_special_chars_returns_201(client, db):
    user = create_test_user(db, email="rc-allowed@example.com")
    headers = auth_headers_for(client, user.email)
    response = client.post(
        "/api/v1/roles",
        json={"name": "super_role-1"},
        headers=headers,
    )
    assert response.status_code == 201


def test_create_role_duplicate_returns_409(client, db):
    ensure_canonical_roles(db)
    user = create_test_user(db, email="rc-dup@example.com")
    headers = auth_headers_for(client, user.email)
    response = client.post(
        "/api/v1/roles",
        json={"name": "gestor"},
        headers=headers,
    )
    assert response.status_code == 409


def test_create_role_duplicate_case_insensitive_returns_409(client, db):
    ensure_canonical_roles(db)
    user = create_test_user(db, email="rc-dup-ci@example.com")
    headers = auth_headers_for(client, user.email)
    response = client.post(
        "/api/v1/roles",
        json={"name": "GESTOR"},
        headers=headers,
    )
    assert response.status_code == 409


# ── GET /roles/{id} ──────────────────────────────────────────────────


def test_get_role_existing_returns_200(client, db):
    admin_role, _ = ensure_canonical_roles(db)
    user = create_test_user(db, email="rg@example.com")
    headers = auth_headers_for(client, user.email)
    response = client.get(f"/api/v1/roles/{admin_role.id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "admin"


def test_get_role_inexistent_returns_404(client, db):
    user = create_test_user(db, email="rg-404@example.com")
    headers = auth_headers_for(client, user.email)
    response = client.get("/api/v1/roles/999999", headers=headers)
    assert response.status_code == 404


# ── PUT /roles/{id} ──────────────────────────────────────────────────


def test_update_role_rename_returns_200(client, db):
    user = create_test_user(db, email="ru-ok@example.com")
    headers = auth_headers_for(client, user.email)
    create_resp = client.post(
        "/api/v1/roles",
        json={"name": "temp-role"},
        headers=headers,
    )
    role_id = create_resp.json()["id"]
    response = client.put(
        f"/api/v1/roles/{role_id}",
        json={"name": "renamed-role"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "renamed-role"


def test_update_role_to_existing_name_returns_409(client, db):
    ensure_canonical_roles(db)
    user = create_test_user(db, email="ru-dup@example.com")
    headers = auth_headers_for(client, user.email)
    create_resp = client.post(
        "/api/v1/roles",
        json={"name": "rename-target"},
        headers=headers,
    )
    role_id = create_resp.json()["id"]
    response = client.put(
        f"/api/v1/roles/{role_id}",
        json={"name": "gestor"},
        headers=headers,
    )
    assert response.status_code == 409


def test_update_role_inexistent_returns_404(client, db):
    user = create_test_user(db, email="ru-404@example.com")
    headers = auth_headers_for(client, user.email)
    response = client.put(
        "/api/v1/roles/999999",
        json={"name": "whatever"},
        headers=headers,
    )
    assert response.status_code == 404


def test_update_role_no_name_keeps_existing(client, db):
    user = create_test_user(db, email="ru-noop@example.com")
    headers = auth_headers_for(client, user.email)
    create_resp = client.post(
        "/api/v1/roles",
        json={"name": "keep-me"},
        headers=headers,
    )
    role_id = create_resp.json()["id"]
    # Update with empty body should be a no-op rename.
    response = client.put(
        f"/api/v1/roles/{role_id}",
        json={},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "keep-me"


# ── DELETE /roles/{id} ───────────────────────────────────────────────


def test_delete_role_unused_returns_204(client, db):
    user = create_test_user(db, email="rd-ok@example.com")
    headers = auth_headers_for(client, user.email)
    create_resp = client.post(
        "/api/v1/roles",
        json={"name": "to-delete"},
        headers=headers,
    )
    role_id = create_resp.json()["id"]
    response = client.delete(f"/api/v1/roles/{role_id}", headers=headers)
    assert response.status_code == 204


def test_delete_role_in_use_returns_409(client, db):
    _, gestor_role = ensure_canonical_roles(db)
    user = create_test_user(db, email="rd-inuse@example.com")
    headers = auth_headers_for(client, user.email)
    # ``user`` ya tiene asignado ``gestor`` por ``create_test_user``.
    response = client.delete(f"/api/v1/roles/{gestor_role.id}", headers=headers)
    assert response.status_code == 409


def test_delete_role_inexistent_returns_404(client, db):
    user = create_test_user(db, email="rd-404@example.com")
    headers = auth_headers_for(client, user.email)
    response = client.delete("/api/v1/roles/999999", headers=headers)
    assert response.status_code == 404
