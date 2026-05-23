from app.tests.fixtures.sources import bypass_url_validation, bypass_rss_content_validation, gestor_user, gestor_headers, admin_user, category
from app.modules.sources.models import RSSChannel

## TESTS: Categories 

def test_create_category(client, gestor_headers):
    response = client.post(
        "/api/v1/categories",
        json={
            "name": "Ciencia y tecnología",
            "source": "IPTC",
        },
        headers=gestor_headers,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Ciencia y tecnología"
    assert data["source"] == "IPTC"
    assert data["code"] == "13000000"

def test_create_invalid_category(client, gestor_headers):
    response = client.post(
        "/api/v1/categories",
        json={
            "name": "Categoria inventada",
            "source": "IPTC",
        },
        headers=gestor_headers,
    )

    assert response.status_code == 400

def test_create_category_invalid_code_pair(client, gestor_headers):
    response = client.post(
        "/api/v1/categories",
        json={
            "name": "Ciencia y tecnología",
            "source": "IPTC",
            "code": "99999999",
        },
        headers=gestor_headers,
    )

    assert response.status_code == 400

## TESTS: Rss Channels

def test_create_rss_channel(
    client,
    gestor_headers,
    category,
    monkeypatch
):
    bypass_url_validation(monkeypatch)
    bypass_rss_content_validation(monkeypatch)
    source_response = client.post(
        "/api/v1/information-sources",
        json={
            "name": "BBC_test",
            "url": "https://bbc.com",
        },
        headers=gestor_headers,
    )

    source_id = source_response.json()["id"]

    assert source_response.status_code == 201

    response = client.post(
        f"/api/v1/information-sources/{source_id}/rss-channels",
        json={
            "url": "https://bbc.com/rss",
            "category_id": category.id,
        },
        headers=gestor_headers,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["information_source_id"] == source_id
    assert data["category_id"] == category.id

def test_duplicate_rss_channel_normalized_url(
    client,
    gestor_headers,
    category,
    monkeypatch
):
    bypass_url_validation(monkeypatch)
    bypass_rss_content_validation(monkeypatch)
    source = client.post(
        "/api/v1/information-sources",
        json={
            "name": "BBC_test",
            "url": "https://bbc.com",
        },
        headers=gestor_headers,
    ).json()

    source_id = source["id"]

    client.post(
        f"/api/v1/information-sources/{source_id}/rss-channels",
        json={
            "url": "HTTPS://BBC.COM/RSS/",
            "category_id": category.id,
        },
        headers=gestor_headers,
    )

    response = client.post(
        f"/api/v1/information-sources/{source_id}/rss-channels",
        json={
            "url": "https://bbc.com/rss",
            "category_id": category.id,
        },
        headers=gestor_headers,
    )

    assert response.status_code == 409

def test_activate_deactivate_rss_channel(
    db,
    client,
    gestor_headers,
    category,
    monkeypatch
):
    bypass_url_validation(monkeypatch)
    bypass_rss_content_validation(monkeypatch)
    source = client.post(
        "/api/v1/information-sources",
        json={
            "name": "BBC_test",
            "url": "https://bbc.com",
        },
        headers=gestor_headers,
    ).json()

    source_id = source["id"]

    channel = client.post(
        f"/api/v1/information-sources/{source_id}/rss-channels",
        json={
            "url": "https://bbc.com/rss",
            "category_id": category.id,
        },
        headers=gestor_headers,
    ).json()

    channel_id = channel["id"]

    response = client.patch(
        f"/api/v1/information-sources/{source_id}/rss-channels/{channel_id}/deactivate",
        headers=gestor_headers,
    )

    assert response.status_code == 200

    rss_channel = db.query(RSSChannel).filter(RSSChannel.id == response.json()["id"]).first()
    assert rss_channel.is_active is False


    response = client.patch(
        f"/api/v1/information-sources/{source_id}/rss-channels/{channel_id}/activate",
        headers=gestor_headers,
    )

    assert response.status_code == 200
    
    rss_channel = db.query(RSSChannel).filter(RSSChannel.id == response.json()["id"]).first()
    assert rss_channel.is_active is True

