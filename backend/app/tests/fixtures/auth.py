import pytest
from app.tests.conftest import client

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
def auth_token(client, registered_user):
    response = client.post("/api/v1/auth/login", json={
        "email": registered_user["email"],
        "password": registered_user["password"]
    })
    return response.json()["access_token"]