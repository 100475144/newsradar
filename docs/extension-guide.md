# Guía de extensión

Cómo añadir nueva funcionalidad sin romper lo existente. La arquitectura
modular del backend (API → Service → Repository) está pensada para
modificarse rápido — la "competición" del enunciado.

## Añadir un módulo nuevo

Estructura recomendada:

```
backend/app/modules/<modulo>/
├── __init__.py
├── models.py        # ORM SQLAlchemy
├── schemas.py       # Pydantic
├── repository.py    # Solo queries
├── service.py       # Lógica de negocio
└── api.py           # FastAPI APIRouter
```

Pasos:

1. **Crear el modelo** en `models.py` heredando de `Base`. Si tienes FKs a
   tablas existentes, importa solo los nombres por string para evitar
   ciclos: `ForeignKey("users.id", ondelete="CASCADE")`.
2. **Schemas Pydantic** en `schemas.py` con `model_config = ConfigDict(from_attributes=True)`
   para serializar desde modelos ORM.
3. **Repositorio** en `repository.py`: clase con `__init__(self, db: Session)`
   y métodos `create`, `get_by_id`, `list_for_user`, etc.
4. **Service** en `service.py` que use el repositorio. Aquí van las
   excepciones HTTP (`raise HTTPException(404, ...)`).
5. **API** en `api.py`: `router = APIRouter(prefix="/<modulo>")`. Inyecta el
   service vía `Depends`.
6. **Registrar el router** en `app/api/router.py` y, si tienes nuevas
   tablas, importar los modelos en `app/alembic/env.py` para que Alembic
   los detecte.
7. **Migración Alembic**:
   ```bash
   docker compose exec api sh -c "cd /code/app && alembic revision -m 'create <modulo>'"
   ```
   Edita el archivo generado y ejecuta `alembic upgrade head`.
8. **Tests**: añade `app/tests/test_<modulo>.py` reutilizando los helpers
   de `app/tests/helpers.py` (`create_test_user`, `auth_headers_for`).

## Añadir un canal RSS al catálogo por defecto

`app/core/seed_sources.py` contiene la lista `RSS_SEEDS_RAW`. Cada entrada
es una tupla `("Medio - Sección", url_rss, codigo_iptc)`. Por ejemplo:

```python
("BBC - Technology", "https://feeds.bbci.co.uk/news/technology/rss.xml", "science_technology"),
```

Restricciones:

- El `codigo_iptc` debe pertenecer a `IPTC_CATEGORY_CODES` (ver `app/core/iptc.py`).
- La URL debe ser única (la unique constraint la rechaza si no).
- Tras añadir, `seed_default_sources(db)` lo recoge en el siguiente arranque
  (es idempotente, no duplica si ya existe).

## Añadir una nueva categoría IPTC

Si el profesor publica una nueva categoría primer nivel:

1. Editar `app/core/iptc.py` y añadir `(codigo, label_humano)` al diccionario.
2. Crear migración Alembic con `INSERT INTO categories (name, source) VALUES (:code, 'IPTC')`.
3. Reiniciar el backend: `_ensure_canonical_roles` y `seed_default_sources`
   son idempotentes.

Si quieres un código no-IPTC, modifica el regex `pattern="^IPTC$"` en
`CategoryBase.source` para aceptar otros valores.

## Añadir un canal de notificación

Hoy soportamos in-app + email (SMTP). Para añadir, p. ej., **Slack**:

1. Crear `app/modules/notifications/slack_utils.py` con
   `send_slack_notification(channel, title, body)`.
2. Añadir las variables `SLACK_WEBHOOK_URL`, etc. a `app/core/config.py` y
   a los dos `.env.example`.
3. Añadir `notify_slack: bool` al modelo `Alert` (migración Alembic).
4. En `alerts/matching.py::process_alerts_for_news`, después del bloque
   `if alert.notify_email`:
   ```python
   if alert.notify_slack:
       send_slack_notification(...)
   ```
5. Frontend: añadir checkbox `notify_slack` en `AlertsPage.jsx`.

El motor de matching está aislado del transporte: cualquier nuevo canal se
añade aquí sin tocar el resto.

## Añadir un endpoint que no esté en la API oficial

Permitido por el profesor (duda 21-abr) con la condición de **no modificar**
los oficiales. Para añadir uno:

1. Crear el handler en el `api.py` del módulo correspondiente.
2. Documentarlo en [`api-design.md`](api-design.md) bajo "Endpoints
   añadidos sobre el contrato oficial".
3. Añadir tests en `app/tests/`.

## Añadir un test backend

Ver [`testing-strategy.md`](testing-strategy.md). Resumen rápido:

- Usa la fixture `client` (TestClient) y `db` (sesión de test).
- Crea usuarios con `create_test_user(db, email=..., role="gestor")`.
- Autentica con `auth_headers_for(client, email)`.

## Añadir una métrica al dashboard

1. Backend: añade método `count_X_for_user(user_id)` al repositorio
   correspondiente y un campo en la respuesta de `/news/me/stats` (o crea
   un endpoint nuevo).
2. Frontend: en `DashboardPage.jsx` consume el endpoint y añade un widget
   (recharts ya está instalado).

## Cambiar el cron del crawler

Variable de entorno `CRAWLER_CRON_EXPRESSION` (5 campos). Por defecto
`*/5 * * * *`. Cambiar en el `.env` raíz y reiniciar el contenedor `api`.
