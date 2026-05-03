from app.tests.fixtures.auth import auth_token, registered_user, user_data, verify_user
from app.tests.fixtures.sources import manager_user_data, reader_user_data, registered_manager, registered_reader, verify_manager, verify_reader, manager_token, reader_token, source_data
from app.tests.conftest import client
from app.modules.sources.models import Source

############ TESTS GET /api/v1/sources ############

def test_list_sources(client, auth_token):
    response = client.get(
        "/api/v1/sources",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200

def test_list_sources(client, manager_token, source_data):
    client.post("/api/v1/sources", json=source_data,
                headers={"Authorization": f"Bearer {manager_token}"})

    response = client.get(
        "/api/v1/sources",
        headers={"Authorization": f"Bearer {manager_token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data) >= 1
    assert any(s["url"] == source_data["url"] for s in data)

############ TESTS POST /api/v1/sources ############

def test_create_source(client, auth_token, source_data):
    response = client.post(
        "/api/v1/sources",
        json=source_data,
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 201

def test_create_source_success(client, db, manager_token, source_data):
    response = client.post(
        "/api/v1/sources",
        json=source_data,
        headers={"Authorization": f"Bearer {manager_token}"}
    )

    assert response.status_code == 201
    data = response.json()

    assert data["url"] == source_data["url"]
    assert data["is_active"] is True

    source = db.query(Source).filter_by(url=source_data["url"]).first()
    assert source is not None
    assert source.name == source_data["name"]

def test_create_source_forbidden(client, reader_token, source_data):
    response = client.post(
        "/api/v1/sources",
        json=source_data,
        headers={"Authorization": f"Bearer {reader_token}"}
    )

    assert response.status_code == 403

def test_create_source_duplicate(client, manager_token, source_data):
    client.post("/api/v1/sources", json=source_data,
                headers={"Authorization": f"Bearer {manager_token}"})

    response = client.post("/api/v1/sources", json=source_data,
                           headers={"Authorization": f"Bearer {manager_token}"})

    assert response.status_code == 400

############ TESTS GET /api/v1/sources/catalog/summary ############

def test_catalog_summary(client, manager_token, source_data):
    client.post("/api/v1/sources", json=source_data,
                headers={"Authorization": f"Bearer {manager_token}"})

    response = client.get(
        "/api/v1/sources/catalog/summary",
        headers={"Authorization": f"Bearer {manager_token}"}
    )

    assert response.status_code == 200

    data = response.json()
    assert "total_sources" in data or len(data) > 0

############ TESTS GET /api/v1/sources/{source_id} ############

def test_read_source(client, manager_token, source_data):
    create = client.post("/api/v1/sources", json=source_data,
                         headers={"Authorization": f"Bearer {manager_token}"})

    source_id = create.json()["id"]

    response = client.get(
        f"/api/v1/sources/{source_id}",
        headers={"Authorization": f"Bearer {manager_token}"}
    )

    assert response.status_code == 200
    assert response.json()["id"] == source_id

def test_read_source_not_found(client, manager_token):
    response = client.get(
        "/api/v1/sources/999",
        headers={"Authorization": f"Bearer {manager_token}"}
    )

    assert response.status_code == 404

############ TESTS PUT /api/v1/sources/{source_id} ############

def test_update_source(client, db, manager_token, source_data):
    create = client.post("/api/v1/sources", json=source_data,
                         headers={"Authorization": f"Bearer {manager_token}"})

    source_id = create.json()["id"]

    updated = {
        "name": "Updated Source",
        "medium_name": "Updated Medium",
        "url": source_data["url"],
        "category": "society"
    }

    response = client.put(
        f"/api/v1/sources/{source_id}",
        json=updated,
        headers={"Authorization": f"Bearer {manager_token}"}
    )

    assert response.status_code == 200

    # DB check
    source = db.query(Source).get(source_id)
    assert source.name == "Updated Source"

############ TESTS DELETE /api/v1/sources/{source_id} ############

def test_delete_source(client, db, manager_token, source_data):
    create = client.post("/api/v1/sources", json=source_data,
                         headers={"Authorization": f"Bearer {manager_token}"})

    source_id = create.json()["id"]

    response = client.delete(
        f"/api/v1/sources/{source_id}",
        headers={"Authorization": f"Bearer {manager_token}"}
    )

    assert response.status_code == 204

    # DB check
    source = db.query(Source).get(source_id)
    assert source is None

############ TESTS PATCH /api/v1/sources/{source_id}/activate ############

def test_activate_source(client, db, manager_token, source_data):
    create = client.post("/api/v1/sources", json=source_data,
                         headers={"Authorization": f"Bearer {manager_token}"})

    source_id = create.json()["id"]

    client.patch(f"/api/v1/sources/{source_id}/deactivate",
                 headers={"Authorization": f"Bearer {manager_token}"})

    response = client.patch(
        f"/api/v1/sources/{source_id}/activate",
        headers={"Authorization": f"Bearer {manager_token}"}
    )

    assert response.status_code == 200

    source = db.query(Source).get(source_id)
    assert source.is_active is True

############ TESTS PATCH /api/v1/sources/{source_id}/deactivate ############

def test_deactivate_source(client, db, manager_token, source_data):
    create = client.post("/api/v1/sources", json=source_data,
                         headers={"Authorization": f"Bearer {manager_token}"})

    source_id = create.json()["id"]

    response = client.patch(
        f"/api/v1/sources/{source_id}/deactivate",
        headers={"Authorization": f"Bearer {manager_token}"}
    )

    assert response.status_code == 200

    source = db.query(Source).get(source_id)
    assert source.is_active is False
