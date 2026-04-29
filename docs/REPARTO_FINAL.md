# Reparto de tareas finales — NEWSRADAR

**Última actualización:** 29 abril 2026 (tras pull + dudas 28-abr).

Este documento se cruza con:
- `DOSS-CHECKLIST_2026` (40 checks de proyecto + 26 de proceso)
- Adenda oficial: desaparece el rol "lector"
- Dudas resueltas del 21 y 28 de abril (cambian el modelo de datos del dashboard)

Cada persona trabaja en `feature/<nombre>-<tema>` y abre PR a `main` con review de mínimo 1 compañero.

---

## 📢 Cambios oficiales sobre el enunciado

### CAMBIO #1 — Desaparece el rol "lector"
- Solo existen gestores (más admin = gestor inicial).
- El **API debe seguir soportando** creación y asignación de roles.
- Cualquier UX condicionada por `role == "lector"` queda obsoleta.

### CAMBIO #1bis — Asignación automática de rol "gestor" (oficial)
> *"Todo nuevo usuario tendrá el rol de 'gestor' automáticamente. Eso sí, el rol de 'admin' debe existir."*

- Operativamente **NO** se asigna rol al registrarse: el rol siempre es `gestor`.
- El rol `admin` se mantiene en el enum y en BD.
- Los endpoints admin de gestión de roles (`PATCH /auth/users/{id}/role`) **se mantienen funcionales** (CAMBIO #1 lo exige), aunque en la práctica solo se usen para promover a admin.

**Estado actual del código**:
- `models.py:20` → `role = Column(String, default="gestor", nullable=False)` ✅ ya correcto
- `schemas.py:88` → aún `UserRole.LECTOR` ❌ T1 lo arregla
- `schemas.py:11` → enum aún incluye `LECTOR` ❌ T1 lo arregla
- Endpoint `PATCH /auth/users/{id}/role` ✅ existe, mantener
- Frontend: `RegisterPage` no debe enviar campo `role` (que use el default de servidor)

### CAMBIO #2 — Dashboard/WordCloud/Stats filtran por alertas del usuario logueado (duda 28-abr)
> "La información se genera solamente con los datos del usuario que está logeado."

- Alertas vuelven a ser **per-usuario** (revertir parte de B1).
- Notificaciones se generan solo para el creador de la alerta (revertir B2).
- Sources y News siguen globales (B0 y B3 quedan correctos).
- WordCloud y Stats: usan únicamente las noticias que matchearon con alertas del usuario logueado.

### CAMBIO #3 — La API debe cumplirse exactamente (duda 21-abr + correo 29-abr + main.py oficial)
- El profesor proporcionó el `main.py` oficial con todos los modelos y endpoints.
- Operaciones y modelos del OpenAPI oficial **no se pueden cambiar**.
- Solo se pueden **añadir** endpoints auxiliares.

#### Discrepancias detectadas (refactor masivo)

**3.1 Prefijo de URL**
- Oficial: `/api/v1/...`
- Nuestro: sin prefijo. **Acción:** añadir prefijo a todos los routers.

**3.2 Modelo `Role` como entidad propia**
- Oficial: `Role{id, name}`. User tiene `role_ids: List[int]` (multi-rol).
- Nuestro: User tiene `role: str` enum.
- **Acción:** crear tabla `roles`, FK many-to-many `user_roles`. Seed: roles `admin` y `gestor`.

**3.3 Modelo `User`**
- Oficial: `email`, `first_name`, `last_name`, `organization` (obligatorio), `role_ids: List[int]`. Password ≥ 6.
- Nuestro: tiene `is_active`, `is_verified` que no están en la API. Mantener internamente, no exponer.
- En register: ignorar `role_ids` del body (CAMBIO #1bis) y forzar role gestor.

**3.4 Modelo `Alert` (correo del profesor)**
```python
name: str (max 200)
descriptors: List[str]               # antes expanded_keywords
categories: List[AlertCategoryItem]  # antes category: str — AlertCategoryItem{code,label}
rss_channels_ids: List[str]          # nuevo
information_sources_ids: List[str]   # nuevo
cron_expression: str (max 120)
```
**Campos que tenemos y NO están** en la API: `keyword`, `notify_in_app`, `notify_email`, `is_active`. Mantener internamente, no exponer en respuestas canónicas.

**3.5 Modelo `Category` como entidad**
- Oficial: `Category{id, name, source="IPTC"}` con CRUD propio en `/api/v1/categories`.
- Nuestro: string libre validado contra dict IPTC.
- **Acción:** crear tabla `categories`, sembrar las 17 IPTC, exponer CRUD.

**3.6 Sources se SPLIT en 2 entidades**
- Oficial:
  - `InformationSource{id, name, url}` — el medio (BBC, El País).
  - `RSSChannel{id, url, category_id, information_source_id}` — el feed concreto.
- Nuestro: tabla única `Source` que mezcla.
- **Acción:** dividir en `information_sources` + `rss_channels` con FK. Endpoints anidados:
  - `/api/v1/information-sources/{source_id}/rss-channels/{channel_id}`

**3.7 Modelo `Notification` (abstracto raro)**
- Oficial: `Notification{timestamp, metrics: List[Metric{name, value: float}]}`. **No tiene** title ni message.
- Nuestro: title, message, summary, etc.
- **Acción:** mantener nuestros campos internamente. La respuesta canónica solo expone timestamp + metrics. Crear endpoint añadido `/notifications/{id}/details` que devuelve los campos extra.

**3.8 Endpoints anidados**
- Alertas: `/api/v1/users/{user_id}/alerts/{alert_id}` (no `/alerts/`).
- Notificaciones: `/api/v1/users/{user_id}/alerts/{alert_id}/notifications/{notification_id}`.
- RSS: `/api/v1/information-sources/{source_id}/rss-channels/{channel_id}`.

**3.9 Endpoints nuevos a implementar**
- `/api/v1/categories` CRUD (5 endpoints).
- `/api/v1/information-sources` CRUD (5 endpoints).
- `/api/v1/information-sources/{id}/rss-channels` CRUD (5 endpoints).
- `/api/v1/stats` CRUD (5 endpoints) — modelo `Stats{id, metrics}`.
- `/api/v1/roles` CRUD (5 endpoints).

**3.10 Endpoints nuestros que NO están en la API oficial — se quedan como añadidos**
- `/news/...` → permitidos por el profesor.
- `/auth/verify-email`, `/auth/resend-verification` → exigidos por el checklist.
- `/auth/users/{id}/role` (cambio rol admin) → necesario por CAMBIO #1.
- Endpoints de matching/dashboard del frontend.

**3.11 Auth**
- Oficial: solo `/api/v1/auth/login` y `/api/v1/auth/register`. Sin verificación.
- Nuestro: añadimos verificación bajo paths extras → permitido.

### CAMBIO #4 — Captura atómica del crawler (duda 21-abr)
- Flujo: lanzar captura → traer noticias → analizar → guardar las que encajan, todo en un proceso.

### CAMBIO #5 — Nubes solo con noticias que encajan en alertas (duda 21-abr)
- Verificar que `/news/wordcloud` filtra por noticias matcheadas, no todas.

---

## 📋 Estado actual frente a los 40 checks del profesor

Leyenda: ✅ hecho · 🟡 parcial · ❌ pendiente

| # | Check | Estado | Notas |
|---|---|---|---|
| 1 | Alertas sobre palabra clave | ✅ | Funciona |
| 2 | Recomienda 3-10 sinónimos | 🟡 | Verificar que recommender devuelve siempre 3-10 |
| 3 | Límite 20 alertas/gestor | 🟡 | `MAX_ALERTS_PER_USER` existe — verificar valor =20 |
| 4 | Selección fuentes específicas para alerta | ✅ | `source_ids` JSONB |
| 5 | Categoría IPTC primer nivel | ✅ | Validación en schemas |
| 6 | Cron expression | ✅ | APScheduler + `CRAWLER_CRON_EXPRESSION` |
| 7 | Clasificación según alerta o fuente | ✅ | `resolve_news_classification` |
| 8 | Email al detectar match | ✅ | MailHog |
| 9 | Mensaje al buzón interno | ✅ | Notificaciones |
| 10 | Título "Actualización de [alerta] en [día/hora]" | ✅ | Formato dd/mm/yyyy HH:MM |
| 11 | Resumen del RSS en notificación | ✅ | Hecho |
| 12 | Alta de canales RSS asociados a un medio | ✅ | `medium_name` |
| 13 | Mínimo 100 canales | ✅ | 104 sembrados |
| 14 | ≥10 medios diferentes | ✅ | 14+ |
| 15 | Canales para todas las cat IPTC | ✅ | 17 categorías cubiertas |
| 16 | Roles "Gestor" y "Lector" definidos | ⚠️ | **Adenda elimina lector** — ver tarea T1 |
| 17 | Lector bloqueado en alertas | ⚠️ | **Adenda elimina lector** — N/A |
| 18 | Email + nombre + apellidos + organización | 🟡 | Existe, pero `organization` es opcional. Ver T2 |
| 19 | Email de verificación | ✅ | |
| 20 | Token expira a 24h | ✅ | |
| 21 | Admin inicial | ✅ | Seed en `main.py` |
| 22 | Nubes palabras por categoría | 🟡 | Hecho pero **debe filtrar por alertas del user** (cambio 28-abr) |
| 23 | Nº total noticias en stats | 🟡 | Hecho pero **debe ser del user logueado** |
| 24 | Alertas por categoría | 🟡 | Igual que arriba |
| 25 | i18n ES/EN | ✅ | react-i18next |
| 26 | API REST | ✅ | FastAPI |
| 27 | OpenAPI documentado | 🟡 | Auto de FastAPI; **verificar matchea API oficial (cambio 21-abr)** |
| 28 | GET /api/v1/health | ✅ | |
| 29 | Almacena noticias y entidades | ✅ | Postgres |
| 30 | Código en GitHub | ✅ | |
| 31 | Documentación Markdown | ✅ | |
| 32 | ADRs en `/docs/adr` | ❌ | Están en `/docs/decisions` |
| 33 | Diagramas de arquitectura | ❌ | No existen |
| 34 | Pruebas automatizadas en CI | 🟡 | CI corre pytest pero faltan tests |
| 35 | GitHub Actions para despliegue | 🟡 | CI sí, **CD no** |
| 36 | Métricas calidad (SonarQube) | ❌ | |
| 37 | Despliegue automático máquina limpia | 🟡 | `docker compose up` lo hace; documentar |
| 38 | Informe cobertura automático | ❌ | `pytest-cov` no integrado |
| 39 | Trazabilidad requisitos-código | ❌ | |
| 40 | Registro de prompts IA | ❌ | |

**Resumen**: 22 ✅ · 11 🟡 · 7 ❌

---

## 🚨 Tareas urgentes derivadas de las dudas (prioridad 0)

| ID | Tarea | Responsable |
|---|---|---|
| **T1** | Eliminar rol lector (enum + default + frontend + migración) | **100475102** |
| **T6** | **Refactor masivo: alinear backend con `main.py` oficial** (T6.1–T6.7) | **Cristina + Manso (frontend)** |
| **T2** | ~~Revertir alertas a per-usuario~~ — **absorbido en T6.4** | (T6) |
| **T3** | ~~Revertir notificaciones a creador~~ — **absorbido en T6.5** | (T6) |
| **T8** | ~~Organization obligatoria~~ — **absorbido en T6.7** | (T6) |
| **T4** | Filtrar dashboard/wordcloud/stats por user logueado (tras T6) | **Manso** |
| **T5** | `/news/wordcloud` solo con noticias matcheadas (tras T6) | **Manso** |
| **T7** | Verificar atomicidad del crawler | **100475101** |
| **T9** | Recommender devuelve 3-10 (checklist #2) | **100475101** |
| **T10** | Límite 20 alertas/gestor (checklist #3) | **100475101** |

---

## 📦 Tareas pendientes del checklist

| ID | Tarea | Check # | Responsable |
|---|---|---|---|
| D1 | Mover ADRs a `/docs/adr` | 32 | **Cristina** |
| D2 | Diagramas arquitectura (bloques + secuencia + despliegue) | 33 | **Cristina** |
| D3 | `architecture.md`, `api-design.md`, `database-design.md` | — | **Cristina** |
| D4 | Trazabilidad requisitos↔código | 39 | **Cristina** |
| D5 | Registro prompts IA `docs/ai-prompts.md` | 40 | **Cristina** |
| D6 | `.env.example` raíz + backend (variables de entorno, no subir secretos) | — | **Cristina** |
| TS1 | Blindaje `conftest.py` contra BD producción | — | **Adrian** |
| TS2 | Tests backend ampliados (auth, sources, alertas per-user) | 34 | **Adrian** |
| TS3 | Cobertura `pytest-cov` integrada en CI | 38 | **Adrian** |
| TS4 | Smoke tests frontend (vitest) | 34 | **100475102** |
| TS5 | Tests crawler (success, error, dedup) | 34 | **100475101** |
| CD1 | CD: build + push imágenes a ghcr.io en push a main | 35 | **Javier** |
| CD2 | Documentar despliegue en máquina limpia (`docs/deployment.md`) | 37 | **Javier** |
| CD3 | SonarCloud o métricas en CI | 36 | **Javier** |

---

## Tareas detalladas

### 🧑‍💻 100475102

#### T1 — Eliminar rol lector + asignación automática gestor (cubre CAMBIO #1 y #1bis)
1. `backend/app/modules/auth/schemas.py:11` → quitar `LECTOR = "lector"`. Dejar solo `ADMIN` y `GESTOR`.
2. `backend/app/modules/auth/schemas.py:88` → default `UserRole.GESTOR`.
3. En `UserCreate`/`RegisterPayload`: si tiene campo `role`, **eliminarlo**. El rol no se acepta en el body de registro; siempre es `gestor` por defecto del modelo.
4. En `auth/service.py::register_user`: ignorar cualquier `role` que viniera en `user_data` (forzar `gestor`).
5. `frontend/src/pages/RegisterPage.jsx`: si tiene selector de rol, eliminarlo.
6. `frontend/src/pages/AlertsPage.jsx:357` y `SourcesPage.jsx:172` → eliminar `canEdit = user?.role !== 'lector'` y todos los usos.
7. Migración Alembic: `UPDATE users SET role='gestor' WHERE role='lector';`.
8. **Mantener intactos** los endpoints admin de roles (`PATCH /auth/users/{id}/role`) — CAMBIO #1 lo exige.
9. Actualizar `docs/demo.md` y cualquier referencia textual a "lector".

#### T2 — Revertir alertas a per-usuario
1. `backend/app/modules/alerts/repository.py`: `list_for_user(user_id)` debe filtrar por `created_by == user_id` (volver al estado anterior).
2. `alerts/api.py::list_alerts` debe usar `list_for_user(current_user.id)`, no `list_all`.
3. `get_by_id`, `update`, `delete`, `activate/deactivate`: solo el creador puede.
4. `AlertsPage.jsx`: quitar el cartel "Alertas globales del sistema" si lo hay.
5. Test: gestor A crea alerta → gestor B no la ve en su lista.

#### T3 — Revertir notificaciones al creador
1. `backend/app/modules/alerts/matching.py::process_alerts_for_news`: en vez de iterar usuarios, crear notificación e email solo para `alert.owner` (volver al modelo original).
2. Eliminar la lógica de "para cada usuario activo verificado".
3. Test: alerta de gestor A matchea news → solo A recibe notificación.

#### T8 — Organization obligatoria
- `auth/schemas.py:18`: cambiar `organization: Optional[str] = Field(default=None, ...)` por `organization: str = Field(..., min_length=1, max_length=150)`.
- Migración Alembic: rellenar usuarios existentes con valor por defecto.
- Validar en frontend `RegisterPage`.

#### TS4 — Smoke tests frontend
1. `npm i -D vitest @testing-library/react @testing-library/jest-dom jsdom`.
2. Script `"test": "vitest"` en `frontend/package.json`.
3. 3 tests: `LoginPage`, `AlertsPage`, `NewsPage` renderizan elementos clave.

---

### 🧑‍💻 Manso (100474286)

#### T4 — Dashboard filtrado por usuario logueado
- Backend: en endpoints de stats, wordcloud, etc., filtrar por `user_id = current_user.id`.
- Las queries deben encadenar: `News → matched_alerts → alert.created_by == user.id`.
- Si no hay tabla de "matches", crear `notifications` como puente (cada notif es prueba de un match).

#### T5 — WordCloud solo con noticias matcheadas
- En `GET /news/wordcloud`, filtrar las palabras a partir de `News` que tengan al menos una `Notification` para el usuario logueado.
- Verificar tras T4: la nube y las stats coherentes.

---

### 🧑‍💻 Cristina (100475144)

#### T6 — Alinear backend con la API oficial (REFACTOR MASIVO BLOQUEANTE)

**Esta tarea es la más invasiva del proyecto.** Toca prácticamente todos los módulos del backend, todas las migraciones y casi todos los endpoints. Se divide en sub-tareas que pueden mergearse progresivamente.

##### T6.1 — Prefijo `/api/v1` en todos los routers
- En `backend/app/main.py` o `app/api/router.py`, montar todos los routers bajo `/api/v1`.
- Verificar `/api/v1/health` ya existe.
- Frontend: actualizar `frontend/src/api/client.js` para usar el nuevo baseURL.

##### T6.2 — Modelo `Role` como entidad
1. Crear modelo `Role{id, name}` y tabla `roles`.
2. Crear tabla `user_roles` (m:n) o columna `role_ids: List[int]` JSONB en User.
3. Migración Alembic: crear tablas, sembrar roles `admin` y `gestor`, asignar a cada usuario existente el role_id correspondiente al string que tenía.
4. Eliminar columna `role` (string) de `users` tras la migración.
5. Endpoints `/api/v1/roles` CRUD (list/create/get/update/delete) — copiar literal del oficial.
6. `User.role_ids` reemplaza al `role` string en respuestas.
7. En `register`: ignorar `role_ids` del body, asignar el role_id de `gestor` por defecto (CAMBIO #1bis).

##### T6.3 — Reestructurar Sources
1. Crear modelos `InformationSource{id, name, url}` y `RSSChannel{id, url, category_id, information_source_id}`.
2. Crear tabla `categories{id, name, source}` y sembrar las 17 IPTC.
3. Migración Alembic con backfill: por cada source actual, crear un `InformationSource` (usando `medium_name`) y un `RSSChannel` ligado a él (usando `url` y `category` mapeada al `category_id`).
4. Reemplazar tabla `sources` por las dos nuevas. Actualizar FK de `news.source_id` para que apunte a `rss_channels.id` (los IDs deben coincidir tras backfill).
5. Endpoints anidados:
   - `/api/v1/categories` CRUD
   - `/api/v1/information-sources` CRUD
   - `/api/v1/information-sources/{source_id}/rss-channels` CRUD
6. Frontend: reescribir `SourcesPage.jsx` con dos vistas (medios / canales).

##### T6.4 — Alertas con schema oficial
1. En `backend/app/modules/alerts/schemas.py`:
   - Renombrar `expanded_keywords` → `descriptors`.
   - Crear tipo `AlertCategoryItem{code: str, label: str}`.
   - `category: str` → `categories: List[AlertCategoryItem]`.
   - Añadir `rss_channels_ids: List[str]` y `information_sources_ids: List[str]`.
   - Sustituir `source_ids` por los dos nuevos.
   - `name` max 200, `cron_expression` max 120.
   - Mover `keyword`, `notify_in_app`, `notify_email` a schema **interno** (no expuesto en API canónica).
2. Modelo: renombrar columnas, JSONB para arrays. `categories` JSONB de objects.
3. Migración con backfill:
   - `expanded_keywords` → `descriptors` (rename column).
   - `category` (string) → `categories` (array `[{code: x, label: IPTC[x]}]`).
   - `source_ids` (int[]) → `rss_channels_ids` (str[] tras T6.3 mapping).
4. Endpoints anidados oficiales: `/api/v1/users/{user_id}/alerts` CRUD.
5. `matching.py`: actualizar lógica con los dos arrays nuevos.
6. Frontend: dos selectores (canales / medios) en `AlertsPage.jsx`, multi-categoría.

##### T6.5 — Notifications con schema oficial
1. Modelo canónico `Notification{timestamp, metrics: List[Metric{name, value: float}]}`.
2. Mantener nuestros campos extra (title, message, summary, news_id) en el modelo BD.
3. Endpoints canónicos anidados: `/api/v1/users/{user_id}/alerts/{alert_id}/notifications` CRUD.
4. Endpoint añadido: `/api/v1/users/{user_id}/alerts/{alert_id}/notifications/{id}/details` con la info enriquecida que necesita el frontend.
5. Migración: rellenar `timestamp` y `metrics` en notificaciones existentes.

##### T6.6 — Stats endpoint nuevo
1. Modelo `Stats{id, metrics: List[Metric]}` y tabla `stats`.
2. Endpoints `/api/v1/stats` CRUD.
3. Generar `Stats` snapshots periódicamente (¿al final de cada ciclo del crawler?).

##### T6.7 — User schema oficial
- Mantener `is_active`, `is_verified` internos, no en respuestas.
- Añadir `organization` obligatoria (T8).
- Endpoints `/api/v1/users` CRUD oficiales.
- Conservar nuestros endpoints añadidos: verificación email + cambio rol admin.

**Entregables**:
- Migración Alembic global con backfill.
- Schemas alineados con `main.py` oficial.
- Routers anidados con prefijo `/api/v1`.
- Frontend adaptado a la nueva estructura.
- `docs/api-design.md` con traza punto-a-punto vs el oficial.

**ATENCIÓN — coordinación necesaria**:
- T2/T3 (revertir alertas y notif a per-user) **se hacen DENTRO de T6.4 y T6.5** porque al rehacer los endpoints ya quedan per-user nativamente (el oficial usa `/users/{user_id}/alerts/...`).
- T8 (organization obligatoria) se hace dentro de T6.7.
- T1 (rol lector) puede mergearse antes de T6 sin problema.
- Tests existentes (auth, news_classification, etc.) van a romperse. Coordinar con Adrian para reescribirlos sobre la nueva estructura.

#### D6 — `.env.example`
Crear:
- `.env.example` raíz: variables del docker-compose (POSTGRES_USER/PASSWORD/DB, SMTP_HOST/PORT, JWT_SECRET, ADMIN_EMAIL, etc.).
- `backend/.env.example`: detalle de cada variable que lee `app/core/config.py`.
- Comentario por variable indicando si tiene default y rango.

#### D1 — Mover ADRs
- `git mv docs/decisions docs/adr`.
- Actualizar links en `docs/README.md`.

#### D2 — Diagramas
- `docs/diagrams/architecture.png` (bloques: backend, frontend, DB, MailHog, scheduler).
- `docs/diagrams/sequence-notification.png` (RSS → crawler → news → matching → notif).
- `docs/diagrams/deployment.png` (containers Docker Compose).
- Incluir fuente PlantUML/Mermaid.

#### D3 — Documentación técnica
- `architecture.md`: módulos, capas, decisiones (apoyado en D2).
- `api-design.md`: endpoints, ya empezado en T6.
- `database-design.md`: ER + tablas + migraciones Alembic.
- `extension-guide.md`: cómo añadir módulo / canal / categoría.
- `testing-strategy.md`: niveles, comandos, conftest blindado.

#### D4 — Trazabilidad
- `docs/traceability.md`: tabla de 4 columnas — Requisito (enunciado) | Historia de Usuario | Archivo(s) código | Test(s).

#### D5 — Prompts IA
- `docs/ai-prompts.md`: prompts clave usados durante el desarrollo, fechas, propósito, modelo (Claude/Copilot/etc.).

---

### 🧑‍💻 100475101

#### T7 — Atomicidad crawler
- Verificar en `crawler/scheduler.py` que el ciclo `fetch → parse → match → save` ocurre en una sola transacción/proceso.
- Si está separado (ej. cron de matching aparte del crawler), unificar.

#### T9 — Recommender 3-10 términos
- Abrir `alerts/recommender.py`.
- Garantizar que `suggest_expanded_keywords()` siempre devuelve entre 3 y 10 términos no vacíos no duplicados.
- Test con 5 keywords.

#### T10 — Límite 20 alertas/gestor
- Confirmar que `MAX_ALERTS_PER_USER == 20` en `alerts/service.py`.
- Test: crear 20 alertas con un gestor → la 21ª devuelve 4xx.

#### TS5 — Tests crawler
- `test_crawler_success.py`: feed mockeado → news creadas.
- `test_crawler_errors.py`: HTTP 500 / malformado / vacío → no rompe.
- `test_crawler_dedup.py`: mismo feed dos veces → sin duplicados.

---

### 🧑‍💻 Adrian (100495924)

#### TS1 — Blindaje `conftest.py`
Al inicio de `backend/app/tests/conftest.py`:
```python
import os
db_url = os.getenv("DATABASE_URL", "")
if "_test" not in db_url and "test" not in db_url.split("/")[-1]:
    raise RuntimeError(
        "Refusing to run tests against a non-test DB. "
        "Set DATABASE_URL pointing to a database whose name contains 'test'."
    )
```

#### TS2 — Tests backend ampliados
- `test_auth.py`: registro con organization, login, verificación email, expiración 24h, cambio de rol admin-only, 401 sin token.
- `test_sources.py`: CRUD por gestor, validación IPTC, todos los gestores ven todas las sources.
- `test_alerts_per_user.py`: gestor A crea alerta → gestor B no la ve. Solo A recibe notificación al matchear.

#### TS3 — Cobertura
1. Añadir `pytest-cov` a `backend/requirements.txt`.
2. En el job `backend-test` del CI, correr `pytest --cov=app --cov-report=xml --cov-report=term`.
3. Subir `coverage.xml` como artefacto.
4. Badge en `README.md`.

---

### 🧑‍💻 Javier Martín

#### CD1 — Pipeline despliegue
Ampliar `.github/workflows/ci.yml` (o crear `cd.yml`):
- Job `build-and-push` activado en push a `main` tras CI verde.
- `docker build` para backend y frontend.
- `docker push` a `ghcr.io/<org>/newsradar-backend:<sha>` y `:latest`.
- Login con `GITHUB_TOKEN`.

#### CD2 — Despliegue máquina limpia
- En `docs/deployment.md`: instrucciones paso a paso para clonar repo + crear `.env` + `docker compose up -d`.
- Verificar que con un repo recién clonado y un `.env` válido, todo arranca sin tocar más.

#### CD3 — Métricas calidad
- SonarCloud: action oficial, exige solo `SONAR_TOKEN` como secret.
- Alternativa más ligera: subir reportes de `ruff` y `eslint` como artefactos del CI con badge en README.

---

## Orden de merge

### 🔥 Fase 0 — Día 1 (en paralelo, no se pisan)
- 100475102 → **T1** (rol lector + register sin role) — independiente, rápido.
- 100475101 → **T7, T9, T10** (atomicidad crawler + recommender + límite alertas) — verificaciones rápidas.
- Cristina → **T6.1** (prefijo `/api/v1` en routers) + **T6.2** (Role como entidad) — base para todo.
- Adrian → **TS1** (blindaje conftest, no depende de schema).

### 🔥 Fase 1 — Días 2-5 (T6 grueso, secuencial)
- Cristina + Manso → **T6.3** (split InformationSource + RSSChannel + Categories).
- Cristina + Manso → **T6.4** (Alerts schema oficial + frontend) — depende de T6.3.
- Cristina → **T6.5** (Notifications schema oficial) — depende de T6.4.
- Cristina → **T6.6** (Stats endpoint).
- Cristina → **T6.7** (User schema oficial + organization obligatoria).

> Mergear T6.x progresivamente con feature flags si se puede, o congelar `main` durante esta fase y trabajar en una rama integradora `feature/api-alignment`.

### Fase 2 — Tras T6 mergeado
- Manso → **T4, T5** (dashboard filtrado por user logueado, ya con `Stats` y modelo nuevo).
- Adrian → **TS2** (tests sobre estructura final).
- Cristina → **D6, D1, D2, D3** (env + ADRs + diagramas + docs técnicas).

### Fase 3 — Cierre
- 100475102 → **TS4** (vitest frontend).
- 100475101 → **TS5** (tests crawler).
- Adrian → **TS3** (cobertura en CI).
- Javier → **CD1, CD2, CD3** (CD + deployment + Sonar).
- Cristina → **D4, D5** (trazabilidad + prompts).

---

## Reglas de trabajo

- Una rama por persona-tarea: `feature/<nombre>-<id>` (ej. `feature/100475102-T2-revert-alerts`).
- PR con descripción del check del enunciado que cubre.
- Review mínima de 1 compañero.
- Cada commit con cuenta de la uni (ya configurado en local).
- No push directo a `main`.

---

## Estado final esperado

- ✅ 40/40 checks del checklist
- ✅ 26/26 checks de proceso
- ✅ Modelo de datos coherente con la duda 28-abr
- ✅ API matcheando exactamente la oficial
- ✅ CI + CD verde
- ✅ Cobertura > 60%
- ✅ Documentación completa
