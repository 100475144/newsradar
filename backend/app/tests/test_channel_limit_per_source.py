"""Prueba 4: Verificación de límite de 5 canales por medio.

Garantiza que un medio de comunicación no puede tener más de 5 canales RSS.
"""

from app.tests.helpers import auth_headers_for, create_test_user


def test_max_5_channels_per_information_source(client, db):
    """Verifica que no se pueden crear más de 5 canales para un mismo medio."""
    user = create_test_user(db, email="foxnews-test@example.com")
    headers = auth_headers_for(client, user.email)

    # 1. Crear un medio "FOXNews"
    source_payload = {
        "name": "FOXNews",
        "url": "https://www.foxnews.com",
    }
    source_response = client.post(
        "/api/v1/information-sources",
        json=source_payload,
        headers=headers,
    )
    assert source_response.status_code == 201, source_response.text
    source_id = source_response.json()["id"]

    # 2. Listar categorías para obtener una válida
    cat_response = client.get("/api/v1/categories", headers=headers)
    assert cat_response.status_code == 200
    categories = cat_response.json()
    assert len(categories) > 0
    category_id = categories[0]["code"]  # Usar el primer código IPTC

    # 3. URLs de los 6 canales (según la prueba)
    channel_urls = [
        "https://moxie.foxnews.com/google-publisher/latest.xml",
        "https://moxie.foxnews.com/google-publisher/world.xml",
        "https://moxie.foxnews.com/google-publisher/politics.xml",
        "https://moxie.foxnews.com/google-publisher/science.xml",
        "https://moxie.foxnews.com/google-publisher/health.xml",
        "https://moxie.foxnews.com/google-publisher/sports.xml",
    ]

    # 4. Crear 5 canales exitosamente
    for i, url in enumerate(channel_urls[:5]):
        channel_payload = {
            "url": url,
            "category_id": int(category_id),
        }
        response = client.post(
            f"/api/v1/information-sources/{source_id}/rss-channels",
            json=channel_payload,
            headers=headers,
        )
        assert response.status_code == 201, f"Channel {i+1} failed: {response.text}"
        print(f"✅ Canal {i+1} creado exitosamente")

    # 5. Listar canales para verificar que hay 5
    list_response = client.get(
        f"/api/v1/information-sources/{source_id}/rss-channels",
        headers=headers,
    )
    assert list_response.status_code == 200
    channels = list_response.json()
    assert len(channels) == 5, f"Esperado 5 canales, pero hay {len(channels)}"
    print(f"✅ Verificado: hay exactamente 5 canales para FOXNews")

    # 6. Intentar crear el 6to canal - DEBE FALLAR con 400
    final_channel_payload = {
        "url": channel_urls[5],
        "category_id": int(category_id),
    }
    final_response = client.post(
        f"/api/v1/information-sources/{source_id}/rss-channels",
        json=final_channel_payload,
        headers=headers,
    )
    assert final_response.status_code == 400, (
        f"Esperado 400, pero recibió {final_response.status_code}: {final_response.text}"
    )
    detail = final_response.json()["detail"]
    assert "5" in detail and "RSS" in detail.upper(), f"Mensaje inesperado: {detail}"
    print(f"✅ Canal 6 rechazado correctamente con 400: {detail}")

    # 7. Verificar que sigue habiendo solo 5 canales (no se persiste el 6to)
    final_list_response = client.get(
        f"/api/v1/information-sources/{source_id}/rss-channels",
        headers=headers,
    )
    assert final_list_response.status_code == 200
    final_channels = final_list_response.json()
    assert len(final_channels) == 5, (
        f"Se persiste el 6to canal. Esperado 5, pero hay {len(final_channels)}"
    )
    print(f"✅ Confirmado: siguen siendo 5 canales (sin persistir el 6to)")

    print("\n✅✅✅ PRUEBA 4 APROBADA: Límite de 5 canales por medio funciona correctamente")
