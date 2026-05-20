"""Tests del split de sources en Category + InformationSource + RSSChannel (T6.3)."""

from __future__ import annotations

from app.modules.sources.models import Category
from app.tests.helpers import auth_headers_for, create_test_user
from app.core.iptc import IPTC_CATEGORIES


def test_categories_endpoint_lists_seeded_iptc(client, db):
    # Sembramos 17 IPTC primer nivel manualmente (el lifespan de la app no
    # corre en tests con BD efímera).

    """ iptc_codes = [
        "Artes, cultura, entretenimiento y medios", "conflict_war_peace", "crime_law_justice",
        "disaster_accident", "economy_business_finance", "education", "environment",
        "health", "human_interest", "labour", "lifestyle_leisure", "politics",
        "religion_belief", "Ciencia y tecnología", "society", "sport", "weather",
    ] """


    for code in IPTC_CATEGORIES:
        if not db.query(Category).filter(Category.id == int(code)).first():
            db.add(Category(id=code, name=IPTC_CATEGORIES[code], source="IPTC"))
    db.commit()

    user = create_test_user(db, email="cat-list@example.com")
    headers = auth_headers_for(client, user.email)

    response = client.get("/api/v1/categories", headers=headers)
    assert response.status_code == 200
    body = response.json()
    names = {item["name"] for item in body}
    assert set(IPTC_CATEGORIES.values()).issubset(names)


def test_information_source_crud_round_trip(client, db):
    user = create_test_user(db, email="info-crud@example.com")
    headers = auth_headers_for(client, user.email)

    # Crear
    response = client.post(
        "/api/v1/information-sources",
        json={"name": "TestMedium", "url": "https://example.com/"},
        headers=headers,
    )
    assert response.status_code == 201
    medium_id = response.json()["id"]

    # Leer
    response = client.get(f"/api/v1/information-sources/{medium_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "TestMedium"

    # Actualizar
    response = client.put(
        f"/api/v1/information-sources/{medium_id}",
        json={"name": "TestMedium Renamed"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "TestMedium Renamed"

    # Borrar
    response = client.delete(
        f"/api/v1/information-sources/{medium_id}", headers=headers
    )
    assert response.status_code == 204


def test_nested_rss_channel_crud(client, db):
    user = create_test_user(db, email="rss-crud@example.com")
    headers = auth_headers_for(client, user.email)

    # Asegurar categoría disponible.
    cat = db.query(Category).filter(Category.name == "Ciencia y tecnología").first()
    if cat is None:
        cat = Category(id=13000000 ,name="Ciencia y tecnología", source="IPTC")
        db.add(cat)
        db.commit()
        db.refresh(cat)

    # Crear medio.
    response = client.post(
        "/api/v1/information-sources",
        json={"name": "TestNews", "url": "https://news.example/"},
        headers=headers,
    )
    medium_id = response.json()["id"]

    # Crear canal anidado.
    response = client.post(
        f"/api/v1/information-sources/{medium_id}/rss-channels",
        json={"url": "https://news.example/feed.rss", "category_id": cat.id},
        headers=headers,
    )
    assert response.status_code == 201
    channel = response.json()
    assert channel["information_source_id"] == medium_id
    assert channel["category_id"] == cat.id

    # Listar
    response = client.get(
        f"/api/v1/information-sources/{medium_id}/rss-channels", headers=headers
    )
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_information_source_404_on_missing(client, db):
    user = create_test_user(db, email="404-medium@example.com")
    headers = auth_headers_for(client, user.email)
    response = client.get("/api/v1/information-sources/999999", headers=headers)
    assert response.status_code == 404
