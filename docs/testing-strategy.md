# Estrategia de testing

> Documento técnico generado en Fase 2 (D3).

## Niveles de prueba

| Nivel | Herramienta | Ámbito | Estado |
|---|---|---|---|
| Unitarios backend | `pytest` | Funciones puras (recommender, matching, helpers) | ✅ |
| Integración backend | `pytest` + `TestClient` + Postgres test DB | Endpoints REST, auth, CRUD | ✅ |
| Cobertura backend | `pytest-cov` | Reporte XML+HTML en CI | ✅ (TS3) |
| Smoke frontend | `vitest` + `@testing-library/react` | Render de páginas clave | ✅ |
| **Verificación oficial** (`devops_verifica-main_v2`) | `python run_tests.py --service http://localhost:8000 --all` | 282 casos contractuales sobre el API | **278/282 OK (98.58 %)** — 4 NOK justificados en ADRs |
| E2E | — | — | Fuera de alcance |

## Comandos

### Local (sin Docker)

```bash
# Crear BD de test si no existe
createdb -U user newsradar_test

cd backend
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/newsradar_test \
  pytest app/tests -q --cov=app --cov-report=term-missing
```

### Dentro del contenedor (recomendado)

```bash
docker compose up -d db api

# Crear BD de test
docker compose exec db psql -U user -d news_db -c "CREATE DATABASE newsradar_test;"

# Correr tests con cobertura
docker compose exec api sh -c \
  'cd /code && DATABASE_URL=postgresql+psycopg://user:password@db:5432/newsradar_test \
   pytest app/tests -q --cov=app --cov-report=term-missing'
```

### CI

`.github/workflows/ci.yml` levanta un servicio `postgres:16` con BD
`newsradar_test`, instala dependencias, corre `pytest --cov` y publica el
reporte como artefacto `backend-coverage` (formato XML + HTML, retención 14
días).

## Blindaje de la BD de test (TS1)

`app/tests/conftest.py` aborta si `DATABASE_URL` no apunta a una base de
datos cuyo nombre contenga `"test"`. Esto evita:

- correr `pytest` accidentalmente contra la BD de desarrollo (`news_db`);
- que el `setup_database` (que hace `Base.metadata.drop_all`) destruya
  datos reales.

```python
if "test" not in db_name.lower():
    raise RuntimeError("Refusing to run tests against a non-test database")
```

## Fixtures clave (`conftest.py`)

| Fixture | Scope | Uso |
|---|---|---|
| `setup_database` | session, autouse | Crea/dropea las tablas al inicio/fin de la sesión |
| `db` | function | Sesión SQLAlchemy con rollback al final del test |
| `client` | function | `TestClient(app)` con `override_get_db` apuntando a la sesión `db` |

## Helpers compartidos (`app/tests/helpers.py`)

```python
ensure_canonical_roles(db) -> (admin, gestor)
create_test_user(db, email=..., role="gestor", is_verified=True) -> User
auth_token_for(client, email, password)
auth_headers_for(client, email, password) -> dict
```

Todos los tests `test_auth.py`, `test_sources_split.py` y
`test_alerts_per_user.py` los usan para reducir boilerplate.

## Cobertura de tests actuales

| Archivo | Cubre |
|---|---|
| `test_health.py` | `GET /api/v1/health` |
| `test_auth.py` (TS2) | Registro, validación organization, password ≥ 6, asignación gestor, login bloqueado sin verificar, cambio de rol admin-only |
| `test_sources_split.py` (TS2) | Categories list, InformationSource CRUD, RSSChannel anidado, 404 |
| `test_alerts_per_user.py` (TS2) | Schema oficial, per-user, 403 cross-user, validación cron, límite 20 alertas |
| `test_default_source_catalog.py` | Seed catalog summary, populación correcta de las 3 tablas split |
| `test_news_classification.py` | Lógica de clasificación de noticias |
| `test_news_external_id.py` | Persistencia de external_id largos |
| `test_alert_email_notification.py` | Flujo end-to-end matching → email vía MailHog |

## Convenciones

- **Aislamiento**: cada test corre en su propia transacción (`rollback` al
  final). No hay estado compartido entre tests.
- **Datos**: si necesitas datos sembrados (categorías IPTC, roles…), créalos
  en el propio test o en helpers. **No confiar en el seed del lifespan**:
  el `lifespan` usa el engine de producción, no el de test.
- **Tests externos**: `test_alert_email_notification.py` requiere MailHog
  corriendo (en CI lo levantamos como servicio Docker; en local con
  `docker compose up mailhog`).
- **Naming**: `test_<accion>_<estado_esperado>` (ej.
  `test_register_requires_organization`).
