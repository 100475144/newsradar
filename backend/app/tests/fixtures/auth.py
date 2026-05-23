import pytest
from app.modules.auth.models import User

@pytest.fixture
def user_data():
    return {
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "organization": "Test Inc",
        "password": "password123"
    }

@pytest.fixture
def registered_user(client, user_data):
    client.post("/api/v1/auth/register", json=user_data)
    return user_data

@pytest.fixture
def verify_user(registered_user, db):
    # Verificar usuario directamente en la BD
    user = db.query(User).filter_by(email=registered_user["email"]).first()
    user.is_verified = True
    db.commit()
    return registered_user

@pytest.fixture
def auth_token(client, verify_user):
    response = client.post("/api/v1/auth/login", json={
        "email": verify_user["email"],
        "password": verify_user["password"]
    })
    return response.json()["access_token"]