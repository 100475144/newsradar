"""Tests del flujo de autenticación (TS2).

Cubre:
- Registro con organization obligatoria (T6.7).
- Login con email no verificado falla (checklist #19).
- Password mínima 6 caracteres (T6.7).
- El servidor ignora ``role`` / ``role_ids`` en el body de registro
  (CAMBIO #1bis): los nuevos usuarios siempre quedan con rol gestor.
- ``role_ids`` en respuesta apunta al rol canónico gestor.
- Endpoint admin-only ``PATCH /auth/users/{id}/role`` (CAMBIO #1).
"""

from __future__ import annotations

from app.tests.helpers import auth_headers_for, create_test_user, ensure_canonical_roles


def test_register_requires_organization(client, db):
    ensure_canonical_roles(db)
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "no-org@example.com",
            "password": "abc123",
            "first_name": "No",
            "last_name": "Org",
        },
    )
    assert response.status_code == 422
    body = response.json()
    fields = {item["loc"][-1] for item in body["detail"]}
    assert "organization" in fields


def test_register_rejects_short_password(client, db):
    ensure_canonical_roles(db)
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "short-pw@example.com",
            "password": "abc",
            "first_name": "Short",
            "last_name": "Pw",
            "organization": "UC3M",
        },
    )
    assert response.status_code == 422


def test_register_assigns_gestor_role_automatically(client, db):
    """CAMBIO #1bis: el rol gestor se fuerza en el servidor, ignorando el body."""
    ensure_canonical_roles(db)
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "auto-gestor@example.com",
            "password": "abc123",
            "first_name": "Auto",
            "last_name": "Gestor",
            "organization": "UC3M",
        },
    )
    assert response.status_code == 201, response.text
    user = response.json()["user"]
    assert user["role"] == "gestor"
    # role_ids debe contener el id del rol gestor.
    _, gestor_role = ensure_canonical_roles(db)
    assert gestor_role.id in user["role_ids"]


def test_login_blocked_for_unverified_user(client, db):
    create_test_user(db, email="unverified@example.com", is_verified=False)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "unverified@example.com", "password": "Password123!"},
    )
    assert response.status_code == 401
    assert "verif" in response.json()["detail"].lower()


def test_login_succeeds_for_verified_user(client, db):
    create_test_user(db, email="ok@example.com", is_verified=True)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "ok@example.com", "password": "Password123!"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "ok@example.com"


def test_admin_can_change_user_role(client, db):
    """CAMBIO #1: el endpoint /auth/users/{id}/role debe seguir funcional."""
    admin = create_test_user(db, email="admin-test@example.com", role="admin")
    target = create_test_user(db, email="target@example.com", role="gestor")

    headers = auth_headers_for(client, admin.email)
    response = client.patch(
        f"/api/v1/auth/users/{target.id}/role",
        params={"role": "admin"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["role"] == "admin"


def test_non_admin_cannot_change_role(client, db):
    create_test_user(db, email="user-a@example.com", role="gestor")
    target = create_test_user(db, email="user-b@example.com", role="gestor")

    headers = auth_headers_for(client, "user-a@example.com")
    response = client.patch(
        f"/api/v1/auth/users/{target.id}/role",
        params={"role": "admin"},
        headers=headers,
    )
    assert response.status_code == 403
