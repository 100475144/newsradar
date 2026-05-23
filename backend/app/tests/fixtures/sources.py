import pytest
from app.modules.auth.models import User
from app.modules.sources.models import Category
from app.core.security import get_password_hash

@pytest.fixture
def gestor_user(db):
    user = User(
        email="gestor@example.com",
        first_name="gestor",
        last_name="test",
        organization="TEST INC",
        hashed_password=get_password_hash("test_pass"),
        is_active=True,
        is_verified=True,
        role="gestor",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def gestor_headers(client, gestor_user):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": gestor_user.email,
            "password": "test_pass",
        },
    )

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }

@pytest.fixture
def admin_user(db):
    user = User(
        email="admin@example.com",
        hashed_password="fake",
        is_active=True,
        is_verified=True,
        role="admin",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def category(db):
    category = db.query(Category).filter(Category.id == 13000000).first()
    if not category:
        category = Category(
            id=13000000,
            name="Ciencia y tecnología",
            source="IPTC",
        )
        db.add(category)
        db.commit()
        db.refresh(category)
    return category

def bypass_url_validation(monkeypatch):

    def fake_url_check(url: str, timeout: float = 2.0):
        return None

    monkeypatch.setattr(
        "app.modules.sources.api._check_url_resolvable",
        fake_url_check,
    )

def bypass_rss_content_validation(monkeypatch):

    def fake_rss_content_check(url: str, timeout: float = 2.0):
        return None

    monkeypatch.setattr(
        "app.modules.sources.api._check_rss_content",
        fake_rss_content_check,
    )
