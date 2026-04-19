# Reparto de tareas finales — NEWSRADAR

Este documento recoge **todo lo que falta** para cerrar el proyecto con nota máxima, cruzando el código actual con:
- La revisión manual del equipo
- El `DOSS-CHECKLIST_2026` que nos dio el profesor (40 preguntas del proyecto + 26 de proceso)
- Los bugs detectados en pruebas entre usuarios

Cada persona trabaja en su rama `feature/<nombre>-<tema>` y abre PR a `main` con review de mínimo 1 compañero.

---

## 🚨 BUGS CRÍTICOS DETECTADOS (prioridad 0)

Confirmados en código, con **causa raíz común**: el sistema trata sources/alertas/news como entidades *per-usuario* en vez de globales.

### B0 — Raíz: seed per-user en `auth/service.py:30`
Al registrarse un usuario, `register_user` llama a `seed_default_sources_for_user(db, user.id)` que **clona las 104 fuentes RSS** marcadas con `created_by = <nuevo user>`. Esto provoca:
- Con N usuarios hay N × 104 sources en BD → trabajo duplicado del crawler y news duplicadas.
- Cada usuario solo ve las news de SUS sources.

**Síntoma reproducible**: un usuario nuevo no ve las noticias antiguas del admin; solo las que el crawler parsea después de su registro (porque esas sí van ligadas a sus copias de sources). Replicar:
1. Admin crea alertas, el crawler corre, genera news.
2. Registrar segundo usuario → ve apartado de news **vacío**.
3. Esperar al siguiente tick del crawler → ahora sí aparecen news (ligadas a sus copias).

### B1 — Alertas personales en vez de globales
`alerts/repository.py::list_for_user` filtra por `created_by == user_id`. Un lector no ve alertas creadas por gestores.

### B2 — Notificaciones solo al creador
`alerts/matching.py:152-156` solo crea notificación/email para `alert.created_by`. Los lectores nunca reciben notificaciones.

### B3 — News filtradas por usuario
`news/repository.py:45` filtra por `Source.created_by == user_id`. Encaja con B0: cada usuario solo ve las news de SUS sources clonadas.

### Modelo de dominio correcto (según enunciado del profesor)
- Sources, alertas y noticias son **entidades globales del sistema**.
- **Gestor/Admin** crea/edita/borra sources y alertas.
- **Lector** ve todo (sources, alertas, news) pero no gestiona.
- **Notificaciones** se generan por usuario: cuando una news hace match con una alerta, se crea una notificación para **cada usuario activo y verificado**.

---

## Resumen del reparto

| # | Tarea | Responsable | Prioridad |
|---|---|---|---|
| B0 | Eliminar seed per-user en registro + sources globales | **100475102** | 🔴 |
| B1 | Fix alertas globales (repositorio + UI + tests) | **100475102** | 🔴 |
| B2 | Fix notificaciones a todos los lectores (matching) | **100475102** | 🔴 |
| B3 | Fix visibilidad de news (todos los autenticados ven todas las noticias) | **100475102** | 🔴 |
| 1 | `.env.example` (raíz + backend) | **Cristina** | 🟡 |
| 2 | Blindaje `conftest.py` contra BD principal | **Adrian** | 🔴 |
| 3 | CI real con GitHub Actions (build + test + lint) | **Javier** | 🔴 |
| 4 | Despliegue automático en pipeline (CD) | **Javier** | 🟡 |
| 5 | Cobertura de pruebas + informe automático | **Adrian** | 🟡 |
| 6 | Tests backend: auth, sources, alertas globales | **Adrian** | 🔴 |
| 7 | Tests crawler (éxito, error, dedup) | **100475101** | 🟡 |
| 8 | Smoke tests frontend (vitest) | **100475102** | 🟡 |
| 9 | Unificar `CRAWLER_CRON_EXPRESSION` en docker-compose | **100475101** | 🔴 |
| 10 | Verificar recommender devuelve 3-10 términos | **100475101** | 🟡 |
| 11 | Verificar límite máximo 20 alertas/gestor | **100475101** | 🟡 |
| 12 | Campo "organización" en registro | **Cristina** | 🟡 |
| 13 | Docs: `architecture.md`, `api-design.md`, `database-design.md` | **Cristina** | 🔴 |
| 14 | Mover ADRs de `docs/decisions` → `docs/adr` | **Cristina** | 🟡 |
| 15 | Diagramas de arquitectura (bloques, flujo, despliegue) | **Cristina** | 🔴 |
| 16 | Trazabilidad requisitos ↔ código (tabla en `docs/`) | **Cristina** | 🟡 |
| 17 | Registro de prompts IA (`docs/ai-prompts.md`) | **Cristina** | 🟡 |
| 18 | Dashboard: nubes de palabras por categoría | **Manso** | 🟡 |
| 19 | Dashboard: nº total noticias + alertas por categoría | **Manso** | 🟡 |
| 20 | i18n ES/EN en frontend | **Manso** | 🟡 |
| 21 | Ocultar acciones al rol lector en la UI | **Manso** | 🟡 |
| 22 | Script/checklist de demo reproducible | **Javier** | 🟡 |
| 23 | SonarQube o métricas de calidad en CI | **Javier** | 🟢 |

🔴 Crítico · 🟡 Importante · 🟢 Deseable

---

## Tareas por persona

### 🧑‍💻 100475102 — Bugs críticos del dominio + frontend tests

**Por qué tú:** hiciste el P4 original de alerts y notifications. Eres quien mejor entiende ese módulo.

#### B0 — Eliminar seed per-user + sources globales
1. En `backend/app/modules/auth/service.py::register_user`, **eliminar** la llamada a `seed_default_sources_for_user(db, user.id)`.
2. Verificar que el seed inicial en `app/main.py::_seed_rss_sources` se ejecuta una sola vez al arranque con el admin como `created_by` (ya está).
3. En `backend/app/modules/sources/repository.py`, sustituir los filtros por `created_by == user_id` en lectura (`list`, `get_by_id`) por **lectura sin filtro**. La escritura sigue gobernada por RBAC en la capa API.
4. Migración Alembic para **limpiar sources duplicadas** de usuarios existentes: mantener solo la copia con `created_by = admin.id` por cada (medium_name, url) y reasignar las news huérfanas a esa copia única.
5. Test: registrar un usuario nuevo → no debe generar sources nuevas; debe ver el catálogo del admin.

#### B1 — Alertas globales
1. En `backend/app/modules/alerts/repository.py`, cambiar `list_for_user(user_id)` para que devuelva **todas** las alertas. Dejar `list_for_user` solo para uso interno si hace falta.
2. El filtrado por rol se hace en API: lector solo lee (ya está), gestor/admin puede gestionar cualquier alerta.
3. En `alerts/service.py`, eliminar `_ensure_sources_owned_by_user` o cambiar la lógica: las fuentes también son globales.
4. Actualizar `AlertsPage.jsx` para mostrar un cartel "Alertas globales del sistema".

#### B2 — Notificaciones para todos los lectores
1. En `backend/app/modules/alerts/matching.py::process_alerts_for_news`:
   - Sustituir `created_by=alert.created_by` por un bucle que cree una notificación por cada usuario activo verificado.
   - Para email, enviar a todos los usuarios con `is_active=True` y `is_verified=True`.
2. Añadir test: al procesar una news matching, se crea N notificaciones (N = nº usuarios).
3. Modelo `Notification` ya tiene `created_by` que aquí pasa a ser `user_id` destinatario; verificar que el endpoint `GET /notifications` filtra por destinatario.

#### B3 — News visibles para todos
1. En `backend/app/modules/news/repository.py`, eliminar el filtro por `Source.created_by == user_id` de `list_news` y `get_by_id_for_user`.
2. Renombrar a `list_news(skip, limit, source_id, category)` y `get_by_id(news_id)`.
3. Actualizar `news/service.py` y `news/api.py` coherentemente.

#### #8 — Smoke tests frontend
1. Instalar vitest: `npm i -D vitest @testing-library/react @testing-library/jest-dom jsdom`.
2. Script `"test": "vitest"` en `frontend/package.json`.
3. 3 tests: `LoginPage` renderiza email/password, `AlertsPage` renderiza botón "Nueva alerta" solo si rol ≠ lector, `NewsPage` renderiza filtro categoría.

**Entregables:** 3 PRs (uno por bug) + 1 PR frontend tests.

---

### 🧑‍💻 Adrian (100495924) — Tests seguros, ampliados y con cobertura

**Por qué tú:** ya hiciste la infraestructura pytest en Docker (Sprint 7 P6).

#### #2 — Blindaje `conftest.py`
1. Al inicio de `backend/app/tests/conftest.py`, forzar que `DATABASE_URL` apunte a BD de test (sufijo `_test` obligatorio).
2. Si la URL coincide con la BD de producción, `raise RuntimeError("Refusing to run tests against production DB")`.
3. Documentar en comentario de cabecera.

#### #6 — Tests backend: auth, sources, alertas globales
- `test_auth.py`: registro, login, verificación email, login con email no verificado (falla), cambio de rol admin-only, 403 para lector intentando crear alerta, campo organización obligatorio.
- `test_sources.py`: CRUD, validación IPTC, activar/desactivar, 403 lector en escritura, **todos los roles ven todas las sources**.
- `test_alerts_global.py`: gestor crea alerta → lector la ve (GET) pero no puede modificar (403). Lector recibe notificación cuando hay match.

#### #5 — Cobertura
1. Añadir `pytest-cov` a `requirements.txt`.
2. Script en `backend/` para correr `pytest --cov=app --cov-report=html --cov-report=xml`.
3. Integrar en el CI (coordinar con Javier): publicar `coverage.xml` como artefacto.

**Entregables:** `conftest.py` blindado + 3 archivos test + cobertura integrada.

---

### 🧑‍💻 100475101 — Crawler y lógica de alertas

**Por qué tú:** eres el "dueño" del crawler desde el Sprint 4.

#### #9 — Unificar config crawler
1. En `docker-compose.yaml` cambiar `CRAWLER_INTERVAL_SECONDS=300` → `CRAWLER_CRON_EXPRESSION=*/5 * * * *`.
2. Eliminar referencias muertas al viejo var en todo el código.
3. Verificar que `scheduler.py` logea la expresión cron al arrancar.

#### #10 — Verificar recommender
1. Abrir `backend/app/modules/alerts/recommender.py`.
2. Garantizar que `suggest_expanded_keywords(keyword)` **siempre** devuelve entre 3 y 10 términos (el profesor lo exige en la checklist #2).
3. Añadir test unitario con 5 keywords distintas.

#### #11 — Verificar límite 20 alertas/gestor
1. En `alerts/service.py::create_alert` ya existe `MAX_ALERTS_PER_USER`. Verificar que vale 20 y es por **gestor**, no por usuario global.
2. Tras el fix de B1 (alertas globales), replantear: ¿cuenta por gestor creador o total del sistema? El enunciado dice "por gestor".
3. Añadir test.

#### #7 — Tests crawler
1. `test_crawler_success.py`: feed mockeado con 3 noticias → 3 `News` creadas.
2. `test_crawler_errors.py`: feed HTTP 500, malformado, vacío → no rompe.
3. `test_crawler_dedup.py`: mismo feed dos veces → sin duplicados.

**Entregables:** docker-compose actualizado + recommender verificado + límite verificado + 3 archivos test.

---

### 🧑‍💻 Cristina (100475144) — Documentación, trazabilidad y extras de registro

**Por qué yo:** tengo visión global del sistema por haber tocado auth, alerts, sources, notifications, seed.

#### #1 — `.env.example`
- `.env.example` en raíz (variables del docker-compose).
- `backend/.env.example` (JWT, SMTP, admin seed, crawler cron).
- Comentario por variable.

#### #12 — Campo organización en registro
- Checklist del profesor #18: registro pide **email, nombre, apellidos y organización**. Actualmente no hay "organización".
- Añadir columna `organization` a `User`, migración Alembic, schema `UserCreate`, formulario frontend `RegisterPage`.

#### #13 — Docs técnicas faltantes
Crear en `docs/`:
- `architecture.md` — módulos, flujo RSS→crawler→news→matching→notif, decisiones clave.
- `api-design.md` — endpoints por módulo, formatos, auth requerida.
- `database-design.md` — ER, tablas, FKs, estrategia migraciones.
- `extension-guide.md` — "cómo añadir módulo / canal / categoría IPTC".
- `testing-strategy.md` — niveles de test, comandos, entorno aislado.

#### #14 — Mover ADRs
- Renombrar `docs/decisions/` → `docs/adr/` (checklist #32 exige `/docs/adr`).
- Actualizar referencias en `docs/README.md`.

#### #15 — Diagramas
- `docs/diagrams/architecture.png` — diagrama de bloques.
- `docs/diagrams/sequence-notification.png` — flujo de alerta→notificación.
- `docs/diagrams/deployment.png` — arquitectura física (Docker Compose).
- Usar draw.io / PlantUML / Mermaid. Exportar PNG + fuente.

#### #16 — Trazabilidad
- `docs/traceability.md`: tabla de 3 columnas — Requisito (enunciado) / Historia de Usuario / Archivo(s) de código / Test(s).

#### #17 — Registro prompts IA
- `docs/ai-prompts.md`: lista de prompts clave usados con Claude/otros, con fecha y propósito. Checklist #40 lo exige.

**Entregables:** 2 `.env.example` + campo organización + 5 docs + 3 diagramas + trazabilidad + prompts.

---

### 🧑‍💻 Manso (100474286) — Frontend UX y dashboard

**Por qué tú:** ya hiciste fixes UI y conoces el frontend.

#### #18 — Nubes de palabras por categoría (checklist #22)
- En `DashboardPage.jsx` añadir nube de palabras por categoría IPTC.
- Librería sugerida: `react-wordcloud` o `@visx/wordcloud`.
- Endpoint auxiliar backend si hace falta: `GET /news/wordcloud?category=X` devuelve top 50 palabras por frecuencia.

#### #19 — Estadísticas globales (checklist #23, #24)
- Total de noticias del sistema.
- Alertas desglosadas por categoría (gráfico barras).
- Librería sugerida: `recharts` (ligera y React-first).

#### #20 — i18n ES/EN (checklist #25)
- Instalar `react-i18next`.
- Traducir literales de: sidebar, dashboard, alerts, sources, news, notifications, login, register.
- Toggle de idioma en la sidebar (banderitas o dropdown).

#### #21 — Ocultar acciones al lector
- Leer rol del contexto de auth.
- En `AlertsPage`, `SourcesPage`: si `role === 'lector'`, ocultar botones Crear / Editar / Eliminar.
- Mostrar badge del rol en sidebar (ya parcialmente hecho).

**Entregables:** dashboard completo + i18n + UX condicionada.

---

### 🧑‍💻 Javier Martín — CI/CD, demo y calidad

**Por qué tú:** PRs transversales, visión conjunta del proyecto.

#### #3 — CI GitHub Actions
Crear `.github/workflows/ci.yml` con jobs:
1. **backend-test**: Postgres de servicio + `pytest --cov=app --cov-report=xml`.
2. **backend-lint**: `ruff check backend/app/`.
3. **frontend-build**: `npm ci && npm run build`.
4. **frontend-test**: `npm test` (depende de que 100475102 merge vitest antes).

Trigger: push a `main`, PRs.

#### #4 — Despliegue automático (CD)
- Job adicional en el workflow: en push a `main` tras CI verde, build de imágenes Docker y publicación a `ghcr.io`.
- Opcional: deployment a máquina limpia documentado en `docs/deployment.md` con `docker compose pull && up -d`.

#### #23 — SonarQube / calidad
- Action `SonarCloud` o al menos generar `pylint`/`ruff` + `eslint` como artefactos del CI.
- Subir `coverage.xml` a SonarCloud o mostrarlo como badge en el README.

#### #22 — Script de demo
`docs/demo.md` checklist:
1. `docker compose up --build`.
2. Login `admin@newsradar.com`.
3. Crear fuente RSS.
4. Gestor crea alerta con categoría IPTC + keyword.
5. Esperar al crawler (o forzar endpoint).
6. Verificar notificación en buzón del **lector** (no solo del gestor).
7. Verificar email en MailHog (http://localhost:8025).

Opcional: `scripts/demo.sh` automatizado por API.

**Entregables:** `ci.yml` verde + CD + métricas calidad + `demo.md`.

---

## Orden de merge recomendado

Para evitar bloqueos por dependencias:

### Semana 1 (en paralelo)
- 100475102 → **B0 primero** (migración de limpieza), luego **B1, B2, B3** (bugs críticos, base para todo)
- Adrian → #2 (blindaje conftest)
- 100475101 → #9 (config crawler)
- Cristina → #1, #12 (env + organización)

### Semana 2 (tras bugs mergeados)
- Adrian → #6 (tests incluyen los nuevos comportamientos globales)
- 100475101 → #7, #10, #11
- 100475102 → #8 (vitest)
- Cristina → #13, #14, #15, #16, #17 (docs)
- Manso → #18, #19, #20, #21

### Semana 3 (tras tests frontend y backend)
- Javier → #3, #4, #22, #23 (CI puede correr todos los tests ya existentes)
- Adrian → #5 (cobertura integrada al CI ya creado)

---

## Reglas de trabajo

- Una rama por persona y tarea: `feature/<nombre>-<tema>` (ej. `feature/adrian-conftest-blindaje`).
- PR a `main` con descripción clara y checklist marcado.
- Review mínima de 1 compañero antes de mergear.
- No push directo a `main`.
- Si un PR bloquea a otro, avisar por el grupo.
- Cada commit con tu cuenta de la uni (ya configurado).

---

## Estado final esperado

Tras completar este reparto, el proyecto cumplirá:
- ✅ 40/40 checks del `DOSS-CHECKLIST_2026` (checklist del profesor)
- ✅ 26/26 checks de proceso general
- ✅ 3 bugs críticos resueltos
- ✅ Sprints 0–8 completados del ROADMAP
- ✅ Entrega final lista

---

## Issue pendiente del compañero

El compañero abrirá una **issue en GitHub** con capturas del fallo: un usuario nuevo no ve las noticias antiguas del admin, pero sí ve las que se parsean después de su registro.

**Causa raíz ya identificada (B0)**: al registrarse cada usuario, `auth/service.py::register_user` ejecuta `seed_default_sources_for_user` que le clona las 104 fuentes RSS con `created_by = nuevo_user`. Como `news/repository.py` filtra news por `Source.created_by == user_id`, cada usuario solo ve las news de sus copias de sources. El crawler parsea todas las copias, por eso las news nuevas sí aparecen (ligadas a las copias del nuevo user) pero las antiguas no (ligadas a las copias del admin).

Ese issue queda cubierto por las tareas **B0 + B3** combinadas. Cuando se mergeen los fixes, cerrar el issue referenciándolo desde el PR.
