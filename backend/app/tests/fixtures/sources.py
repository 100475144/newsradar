import pytest
from app.modules.auth.models import User

@pytest.fixture
def manager_user_data():
    # Usuario Gestor
    return {
        "email": "manager@test.com",
        "first_name": "manager",
        "last_name": "Test",
        "organization": "Test Inc",
        "password": "test_password"
    }

@pytest.fixture
def reader_user_data():
    # Usuario Lector
    return {
        "email": "reader@test.com",
        "first_name": "Reader",
        "last_name": "Test",
        "organization": "Test Inc",
        "password": "test_password"
    }

@pytest.fixture
def registered_manager(client, manager_user_data):
    client.post("/api/v1/auth/register", json=manager_user_data)
    return manager_user_data

@pytest.fixture
def registered_reader(client, reader_user_data):
    client.post("/api/v1/auth/register", json=reader_user_data)
    return reader_user_data

@pytest.fixture
def verify_manager(registered_manager, db):
    # Verificar usuario directamente en la BD
    user = db.query(User).filter_by(email=registered_manager["email"]).first()
    user.is_verified = True
    db.commit()
    return registered_manager

@pytest.fixture
def verify_reader(registered_reader, db):
    # Verificar usuario directamente en la BD
    user = db.query(User).filter_by(email=registered_reader["email"]).first()
    user.is_verified = True
    user.role = "lector"
    db.commit()
    return registered_reader

@pytest.fixture
def manager_token(client, verify_manager):
    response = client.post("/api/v1/auth/login", json={
        "email": verify_manager["email"],
        "password": verify_manager["password"],
    })
    return response.json()["access_token"]


@pytest.fixture
def reader_token(client, verify_reader):
    response = client.post("/api/v1/auth/login", json={
        "email": verify_reader["email"],
        "password": verify_reader["password"],
    })
    return response.json()["access_token"]


@pytest.fixture
def source_data():
    return {
        "medium_name": "Test Medium",
        "name": "Test Source",
        "url": "https://test.com/rss",
        "category": "science_technology"
    }