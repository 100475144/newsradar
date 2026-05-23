from app.tests.fixtures.stats import stats_payload, invalid_stats_payload
from app.modules.stats.models import Stats
from app.tests.fixtures.auth import auth_token, user_data, registered_user, verify_user

## CREATE stats
def test_create_stats_success(client, auth_token, stats_payload):
    response = client.post(
        "/api/v1/stats",
        json=stats_payload,
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 201

    data = response.json()

    assert "id" in data
    assert len(data["metrics"]) == 2
    assert data["metrics"][0]["name"] == "Total Users"
    assert isinstance(data["metrics"][0]["value"], float)

def test_create_stats_persists_in_db(client, auth_token, stats_payload, db):
    response = client.post(
        "/api/v1/stats",
        json=stats_payload,
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    stats_id = response.json()["id"]

    stats_db = db.query(Stats).filter(Stats.id == stats_id).first()

    assert stats_db is not None
    assert stats_db.metrics[0]["name"] == "Total Users"

## LIST stats
def test_list_stats(client, auth_token, stats_payload):
    client.post(
        "/api/v1/stats",
        json=stats_payload,
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    response = client.get(
        "/api/v1/stats",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1

## GET by id
def test_get_stats_by_id(client, auth_token, stats_payload):
    create = client.post(
        "/api/v1/stats",
        json=stats_payload,
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    stats_id = create.json()["id"]

    response = client.get(
        f"/api/v1/stats/{stats_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == stats_id

def test_get_stats_404(client, auth_token):
    response = client.get(
        "/api/v1/stats/999999",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 404

## UPDATE stats
def test_update_stats(client, auth_token, stats_payload):
    create = client.post(
        "/api/v1/stats",
        json=stats_payload,
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    stats_id = create.json()["id"]

    update_payload = {
        "metrics": [
            {"name": "Updated Metric", "value": 999}
        ]
    }

    response = client.put(
        f"/api/v1/stats/{stats_id}",
        json=update_payload,
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200
    assert response.json()["metrics"][0]["name"] == "Updated Metric"

## DELETE stats
def test_delete_stats(client, auth_token, stats_payload, db):
    create = client.post(
        "/api/v1/stats",
        json=stats_payload,
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    stats_id = create.json()["id"]

    response = client.delete(
        f"/api/v1/stats/{stats_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 204

    assert db.query(Stats).filter(Stats.id == stats_id).first() is None

## VALIDACIONES (_normalize_metrics)
def test_create_stats_empty_metrics(client, auth_token):
    response = client.post(
        "/api/v1/stats",
        json={"metrics": []},
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 422

def test_create_stats_empty_name(client, auth_token):
    response = client.post(
        "/api/v1/stats",
        json={"metrics": [{"name": "", "value": 1}]},
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 422

def test_create_stats_none_value(client, auth_token):
    response = client.post(
        "/api/v1/stats",
        json={"metrics": [{"name": "x", "value": None}]},
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 422

def test_create_stats_duplicate_metrics(client, auth_token):
    response = client.post(
        "/api/v1/stats",
        json={
            "metrics": [
                {"name": "Users", "value": 1},
                {"name": "users", "value": 2},
            ]
        },
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 409

def test_create_stats_invalid_value(client, auth_token):
    response = client.post(
        "/api/v1/stats",
        json={"metrics": [{"name": "Users", "value": "abc"}]},
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 422

## /GLOBAL endpoint
def test_global_stats_returns_structure(client, auth_token):
    response = client.get(
        "/api/v1/stats/global",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert "total_news" in data
    assert "total_alerts" in data
    assert "news_by_category" in data

def test_global_stats_categories_sorted(client, auth_token):
    response = client.get(
        "/api/v1/stats/global",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    data = response.json()

    counts = [c["count"] for c in data["news_by_category"]]

    assert counts == sorted(counts, reverse=True)