"""Tests CRUD oficiales del recurso ``User`` (``/api/v1/users``).

Estos tests cubren ``backend/app/modules/auth/users_api.py``, que es
distinto de ``auth/api.py`` (registro/login/verificación, ya cubierto en
``test_auth.py``).

Reglas testadas:
* ``GET /users``: cualquier autenticado.
* ``POST /users``: sólo admin. Asigna gestor por defecto si ``role_ids``
  no llega; rechaza duplicado de email; rechaza más de un role_id;
  rechaza role_id inexistente.
* ``GET /users/{id}``: propio o admin.
* ``PUT /users/{id}``: propio o admin. Cambiar ``role_ids`` requiere admin.
* ``DELETE /users/{id}``: propio o admin.
"""

from __future__ import annotations

from app.modules.auth.models import Role
from app.tests.helpers import (
    auth_headers_for,
    create_test_user,
    ensure_canonical_roles,
)


# ── GET /users ───────────────────────────────────────────────────────


def test_list_users_returns_200_authenticated(client, db):
    user = create_test_user(db, email="lister@example.com")
    headers = auth_headers_for(client, user.email)
    response = client.get("/api/v1/users", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert any(u["email"] == "lister@example.com" for u in body)


def test_list_users_unauthenticated_returns_401(client, db):
    ensure_canonical_roles(db)
    response = client.get("/api/v1/users")
    assert response.status_code == 401


# ── POST /users ──────────────────────────────────────────────────────


def test_create_user_as_admin_returns_201_with_default_gestor(client, db):
    admin = create_test_user(db, email="admin-create@example.com", role="admin")
    headers = auth_headers_for(client, admin.email)
    response = client.post(
        "/api/v1/users",
        json={
            "email": "new@example.com",
            "password": "Password123!",
            "first_name": "New",
            "last_name": "User",
            "organization": "UC3M",
        },
        headers=headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new@example.com"
    assert body["role"] == "gestor"
    _, gestor_role = ensure_canonical_roles(db)
    assert gestor_role.id in body["role_ids"]


def test_create_user_normalizes_email_lowercase(client, db):
    admin = create_test_user(db, email="admin-norm@example.com", role="admin")
    headers = auth_headers_for(client, admin.email)
    response = client.post(
        "/api/v1/users",
        json={
            "email": "MixedCase@Example.COM",
            "password": "Password123!",
            "first_name": "M",
            "last_name": "C",
            "organization": "UC3M",
        },
        headers=headers,
    )
    assert response.status_code == 201
    assert response.json()["email"] == "mixedcase@example.com"


def test_create_user_as_gestor_returns_403(client, db):
    gestor = create_test_user(db, email="gestor-create@example.com")
    headers = auth_headers_for(client, gestor.email)
    response = client.post(
        "/api/v1/users",
        json={
            "email": "x@example.com",
            "password": "Password123!",
            "first_name": "X",
            "last_name": "Y",
            "organization": "UC3M",
        },
        headers=headers,
    )
    assert response.status_code == 403


def test_create_user_duplicate_email_returns_409(client, db):
    admin = create_test_user(db, email="admin-dup@example.com", role="admin")
    create_test_user(db, email="taken@example.com")
    headers = auth_headers_for(client, admin.email)
    response = client.post(
        "/api/v1/users",
        json={
            "email": "taken@example.com",
            "password": "Password123!",
            "first_name": "X",
            "last_name": "Y",
            "organization": "UC3M",
        },
        headers=headers,
    )
    assert response.status_code == 409


def test_create_user_with_multiple_role_ids_returns_400(client, db):
    admin = create_test_user(db, email="admin-multi@example.com", role="admin")
    admin_role, gestor_role = ensure_canonical_roles(db)
    headers = auth_headers_for(client, admin.email)
    response = client.post(
        "/api/v1/users",
        json={
            "email": "multi@example.com",
            "password": "Password123!",
            "first_name": "M",
            "last_name": "R",
            "organization": "UC3M",
            "role_ids": [admin_role.id, gestor_role.id],
        },
        headers=headers,
    )
    assert response.status_code == 400


def test_create_user_with_inexistent_role_id_returns_400(client, db):
    admin = create_test_user(db, email="admin-bad-role@example.com", role="admin")
    headers = auth_headers_for(client, admin.email)
    response = client.post(
        "/api/v1/users",
        json={
            "email": "br@example.com",
            "password": "Password123!",
            "first_name": "B",
            "last_name": "R",
            "organization": "UC3M",
            "role_ids": [99999],
        },
        headers=headers,
    )
    assert response.status_code == 400


def test_create_user_with_valid_role_id_returns_201(client, db):
    admin = create_test_user(db, email="admin-vr@example.com", role="admin")
    _, gestor_role = ensure_canonical_roles(db)
    headers = auth_headers_for(client, admin.email)
    response = client.post(
        "/api/v1/users",
        json={
            "email": "vr@example.com",
            "password": "Password123!",
            "first_name": "V",
            "last_name": "R",
            "organization": "UC3M",
            "role_ids": [gestor_role.id],
        },
        headers=headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert gestor_role.id in body["role_ids"]


# ── GET /users/{id} ──────────────────────────────────────────────────


def test_get_user_own_returns_200(client, db):
    user = create_test_user(db, email="own@example.com")
    headers = auth_headers_for(client, user.email)
    response = client.get(f"/api/v1/users/{user.id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "own@example.com"


def test_get_user_other_as_admin_returns_200(client, db):
    admin = create_test_user(db, email="admin-get@example.com", role="admin")
    other = create_test_user(db, email="other-get@example.com")
    headers = auth_headers_for(client, admin.email)
    response = client.get(f"/api/v1/users/{other.id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "other-get@example.com"


def test_get_user_other_as_gestor_returns_403(client, db):
    user_a = create_test_user(db, email="get-a@example.com")
    user_b = create_test_user(db, email="get-b@example.com")
    headers = auth_headers_for(client, user_a.email)
    response = client.get(f"/api/v1/users/{user_b.id}", headers=headers)
    assert response.status_code == 403


def test_get_user_inexistent_returns_404(client, db):
    admin = create_test_user(db, email="admin-404@example.com", role="admin")
    headers = auth_headers_for(client, admin.email)
    response = client.get("/api/v1/users/999999", headers=headers)
    assert response.status_code == 404


# ── PUT /users/{id} ──────────────────────────────────────────────────


def test_update_user_own_basic_fields_returns_200(client, db):
    user = create_test_user(db, email="upd-own@example.com")
    headers = auth_headers_for(client, user.email)
    response = client.put(
        f"/api/v1/users/{user.id}",
        json={
            "first_name": "Updated",
            "last_name": "Name",
            "organization": "OrgX",
        },
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["first_name"] == "Updated"
    assert body["last_name"] == "Name"
    assert body["organization"] == "OrgX"


def test_update_user_email_normalizes_lowercase(client, db):
    user = create_test_user(db, email="upd-email@example.com")
    headers = auth_headers_for(client, user.email)
    response = client.put(
        f"/api/v1/users/{user.id}",
        json={"email": "NEW-Email@Example.com"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["email"] == "new-email@example.com"


def test_update_user_email_duplicate_returns_409(client, db):
    user_a = create_test_user(db, email="upd-a@example.com")
    create_test_user(db, email="upd-b@example.com")
    headers = auth_headers_for(client, user_a.email)
    response = client.put(
        f"/api/v1/users/{user_a.id}",
        json={"email": "upd-b@example.com"},
        headers=headers,
    )
    assert response.status_code == 409


def test_update_user_password_changes_hash(client, db):
    user = create_test_user(db, email="upd-pw@example.com")
    old_hash = user.hashed_password
    headers = auth_headers_for(client, user.email)
    response = client.put(
        f"/api/v1/users/{user.id}",
        json={"password": "NewPassword123!"},
        headers=headers,
    )
    assert response.status_code == 200
    db.refresh(user)
    assert user.hashed_password != old_hash


def test_update_user_role_as_gestor_returns_403(client, db):
    _, gestor_role = ensure_canonical_roles(db)
    user = create_test_user(db, email="upd-role-gestor@example.com")
    headers = auth_headers_for(client, user.email)
    response = client.put(
        f"/api/v1/users/{user.id}",
        json={"role_ids": [gestor_role.id]},
        headers=headers,
    )
    assert response.status_code == 403


def test_update_user_role_as_admin_returns_200(client, db):
    admin = create_test_user(db, email="admin-upd-role@example.com", role="admin")
    target = create_test_user(db, email="upd-role-target@example.com")
    admin_role, _ = ensure_canonical_roles(db)
    headers = auth_headers_for(client, admin.email)
    response = client.put(
        f"/api/v1/users/{target.id}",
        json={"role_ids": [admin_role.id]},
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert admin_role.id in body["role_ids"]


def test_update_user_role_inexistent_returns_400(client, db):
    admin = create_test_user(db, email="admin-upd-bad@example.com", role="admin")
    target = create_test_user(db, email="upd-role-bad@example.com")
    headers = auth_headers_for(client, admin.email)
    response = client.put(
        f"/api/v1/users/{target.id}",
        json={"role_ids": [99999]},
        headers=headers,
    )
    assert response.status_code == 400


def test_update_user_role_empty_list_removes_roles(client, db):
    admin = create_test_user(db, email="admin-upd-empty@example.com", role="admin")
    target = create_test_user(db, email="upd-role-empty@example.com")
    headers = auth_headers_for(client, admin.email)
    response = client.put(
        f"/api/v1/users/{target.id}",
        json={"role_ids": []},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["role_ids"] == []


def test_update_user_other_as_gestor_returns_403(client, db):
    user_a = create_test_user(db, email="upd-other-a@example.com")
    user_b = create_test_user(db, email="upd-other-b@example.com")
    headers = auth_headers_for(client, user_a.email)
    response = client.put(
        f"/api/v1/users/{user_b.id}",
        json={"first_name": "Hack"},
        headers=headers,
    )
    assert response.status_code == 403


def test_update_user_inexistent_returns_404(client, db):
    admin = create_test_user(db, email="admin-upd-404@example.com", role="admin")
    headers = auth_headers_for(client, admin.email)
    response = client.put(
        "/api/v1/users/999999",
        json={"first_name": "Nope"},
        headers=headers,
    )
    assert response.status_code == 404


# ── DELETE /users/{id} ───────────────────────────────────────────────


def test_delete_user_own_returns_204(client, db):
    user = create_test_user(db, email="del-own@example.com")
    headers = auth_headers_for(client, user.email)
    response = client.delete(f"/api/v1/users/{user.id}", headers=headers)
    assert response.status_code == 204


def test_delete_user_other_as_admin_returns_204(client, db):
    admin = create_test_user(db, email="admin-del@example.com", role="admin")
    other = create_test_user(db, email="del-target@example.com")
    headers = auth_headers_for(client, admin.email)
    response = client.delete(f"/api/v1/users/{other.id}", headers=headers)
    assert response.status_code == 204


def test_delete_user_other_as_gestor_returns_403(client, db):
    user_a = create_test_user(db, email="del-a@example.com")
    user_b = create_test_user(db, email="del-b@example.com")
    headers = auth_headers_for(client, user_a.email)
    response = client.delete(f"/api/v1/users/{user_b.id}", headers=headers)
    assert response.status_code == 403


def test_delete_user_inexistent_returns_404(client, db):
    admin = create_test_user(db, email="admin-del-404@example.com", role="admin")
    headers = auth_headers_for(client, admin.email)
    response = client.delete("/api/v1/users/999999", headers=headers)
    assert response.status_code == 404
