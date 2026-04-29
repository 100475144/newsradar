"""Helpers compartidos para los tests de TS2.

Crean usuarios + login para autenticar requests del TestClient.
"""

from __future__ import annotations

import uuid

from app.core.security import get_password_hash
from app.modules.auth.models import Role, User


def ensure_canonical_roles(db) -> tuple[Role, Role]:
    """Garantiza que existen los roles ``admin`` y ``gestor`` (idempotente)."""
    admin = db.query(Role).filter(Role.name == "admin").first()
    if admin is None:
        admin = Role(name="admin")
        db.add(admin)
        db.flush()
    gestor = db.query(Role).filter(Role.name == "gestor").first()
    if gestor is None:
        gestor = Role(name="gestor")
        db.add(gestor)
        db.flush()
    db.commit()
    return admin, gestor


def create_test_user(
    db,
    *,
    email: str | None = None,
    password: str = "Password123!",
    role: str = "gestor",
    is_verified: bool = True,
    is_active: bool = True,
) -> User:
    admin_role, gestor_role = ensure_canonical_roles(db)

    suffix = uuid.uuid4().hex[:8]
    user = User(
        email=email or f"u-{suffix}@example.com",
        first_name="Test",
        last_name="User",
        organization="UC3M",
        hashed_password=get_password_hash(password),
        role=role,
        is_active=is_active,
        is_verified=is_verified,
    )
    user.roles = [admin_role if role == "admin" else gestor_role]
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def auth_token_for(client, email: str, password: str = "Password123!") -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth_headers_for(client, email: str, password: str = "Password123!") -> dict:
    token = auth_token_for(client, email, password)
    return {"Authorization": f"Bearer {token}"}
