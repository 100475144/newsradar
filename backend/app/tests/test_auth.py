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
from app.tests.fixtures.auth import user_data, registered_user, auth_token, verify_user
from app.modules.auth.models import User
from app.core.security import verify_password, verify_token

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


############ P6

def test_register_success(client, db, user_data):
    response = client.post("/api/v1/auth/register", json=user_data)

    assert response.status_code == 201
    data = response.json()
    
    assert data["user"]["email"] == user_data["email"]
    assert data["user"]["first_name"] == user_data["first_name"]
    assert data["user"]["last_name"] == user_data["last_name"]
    assert data["user"]["organization"] == user_data["organization"]
    assert type(data["user"]["id"]) is int  

    # Valores por defecto en el registro
    assert data["user"]["role"] == "gestor"
    assert data["user"]["is_active"] is True
    assert data["user"]["is_verified"] is False

    assert data["user"]["created_at"] is not None
    assert data["user"]["updated_at"] is not None
   
   # Comprobar datos que se han almacenado en la BD
    user = db.query(User).filter_by(email=user_data["email"]).first()
    assert user is not None
    assert user.email == user_data["email"]
    assert user.first_name == user_data["first_name"]
    assert user.last_name == user_data["last_name"]
    assert user.organization == user_data["organization"]
    assert type(user.id) is int  
    # Verificamos el hash del password
    assert verify_password(user_data["password"], user.hashed_password) is True
    assert user.role == "gestor"
    assert user.is_active is True
    assert user.is_verified is False

    assert user.created_at is not None
    assert user.updated_at is not None


def test_register_duplicate_email(client, user_data, registered_user):
    #client.post("/api/v1/auth/register", json=user_data)

    response = client.post("/api/v1/auth/register", json=user_data)

    assert response.status_code == 400
    assert "A user with this email already exists." in response.json()["detail"]

def test_register_invalid_email(client, user_data):
    user_data["email"] = "invalid-email"

    response = client.post("/api/v1/auth/register", json=user_data)

    assert response.status_code == 422
    assert "value is not a valid email address" in response.json()["detail"][0]["msg"]
    #assert "value is not a valid email address: An email address must have an @-sign."

############ TESTS /api/v1/auth/verify-email ############

############ TESTS /api/v1/auth/resend-verification ############

############ TESTS /api/v1/auth/login ############
def test_login_success(client, verify_user):
    response = client.post("/api/v1/auth/login", json={
        "email": verify_user["email"],
        "password": verify_user["password"]
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Verificar que el token es válido
    token = data["access_token"]
    payload = verify_token(token)
    assert payload["sub"] is not None

def test_login_wrong_password(client, registered_user):
    response = client.post("/api/v1/auth/login", json={
        "email": registered_user["email"],
        "password": "wrongpassword"
    })

    assert response.status_code == 401
    assert "Invalid email or password." in response.json()["detail"]

def test_login_user_not_found(client):
    response = client.post("/api/v1/auth/login", json={
        "email": "noone@test.com",
        "password": "password123"
    })

    assert response.status_code == 401
    assert "Invalid email or password." in response.json()["detail"]

def test_login_inactive_user(client, db, registered_user):
    # desactivar usuario directamente en DB
    user = db.query(User).filter_by(email=registered_user["email"]).first()
    user.is_active = False
    db.commit()
    # verificar usuario en la BD

    response = client.post("/api/v1/auth/login", json={
        "email": registered_user["email"],
        "password": registered_user["password"]
    })

    assert response.status_code == 401
    assert "This user account is inactive." in response.json()["detail"]

############ TESTS /api/v1/auth/token ############

def test_token_success(client, verify_user):
    response = client.post(
        "/api/v1/auth/token",
        data={
            "username": verify_user["email"],
            "password": verify_user["password"]
        }
    )

    assert response.status_code == 200
    assert "access_token" in response.json()

def test_token_invalid_credentials(client):
    response = client.post(
        "/api/v1/auth/token",
        data={
            "username": "wrong@test.com",
            "password": "wrong"
        }
    )

    assert response.status_code == 401
    assert "Invalid email or password." in response.json()["detail"]

############ TESTS /api/v1/auth/me ############
def test_me(client, auth_token):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200
    assert "email" in response.json()

def test_me_no_token(client):
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]

def test_me_invalid_token(client):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalidtoken"}
    )

    assert response.status_code == 401

def test_me_user_deleted(client, db, auth_token, user_data):
    user = db.query(User).filter_by(email=user_data["email"]).first()
    db.delete(user)
    db.commit()

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 401
    assert "Could not validate credentials." in response.json()["detail"]

############ TESTS /api/v1/auth/users ############

############ TESTS /api/v1/auth/users/{user_id}/role ############

