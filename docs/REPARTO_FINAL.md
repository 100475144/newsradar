# Reparto de tareas finales — NEWSRADAR

**Última actualización:** 30 abril 2026 (tras cerrar Fase 2 completa).

Este documento se cruza con:
- `DOSS-CHECKLIST_2026` (40 checks de proyecto + 26 de proceso)
- Adenda oficial: desaparece el rol "lector" (CAMBIO #1)
- Adenda oficial: registro automático con rol gestor (CAMBIO #1bis)
- Dudas 21-abr y 28-abr (CAMBIO #2: dashboards per-user)
- Correo 29-abr + `main.py` oficial del aula global (CAMBIO #3)

Cada persona trabaja en `feature/<nombre>-<tema>` y abre PR a `main` con review de mínimo 1 compañero.

---

## ✅ Estado global de las fases

| Fase | Contenido | Estado |
|---|---|---|
| **Fase 0** | Infra base + cumplir adenda CAMBIO #1/#1bis + verificaciones | ✅ Cerrada (rama `feature/phase0-cristina`) |
| **Fase 1** | Refactor masivo para alinear API con `main.py` oficial (CAMBIO #3) | ✅ Cerrada (rama `feature/phase1-cristina-t6.3-t6.4`) |
| **Fase 2** | Dashboard per-user + tests ampliados + cobertura + documentación + ADRs + diagramas + .env.example | ✅ Cerrada (rama `feature/phase2-cristina`) |
| **Fase 3** | Tests frontend + CD + Sonar + traceability + prompts IA | 🔴 Pendiente |

---

## 📢 Cambios oficiales sobre el enunciado (todos cubiertos)

### CAMBIO #1 — Desaparece el rol "lector" — ✅ Aplicado en Fase 0
- Solo existen gestores (más admin = gestor inicial).
- El **API debe seguir soportando** creación y asignación de roles → endpoints admin se mantienen.
- Cualquier UX condicionada por `role == "lector"` eliminada.

### CAMBIO #1bis — Asignación automática de rol "gestor" — ✅ Aplicado en Fase 0
> *"Todo nuevo usuario tendrá el rol de 'gestor' automáticamente. Eso sí, el rol de 'admin' debe existir."*

- El registro nunca acepta `role` ni `role_ids` en el body.
- El servidor asigna `gestor` automáticamente vía `role_ids` (T6.2).
- El rol `admin` se conserva (seed inicial + endpoints admin).

### CAMBIO #2 — Dashboard/WordCloud/Stats filtran por alertas del usuario logueado — 🟡 Pendiente Fase 2
> *"La información se genera solamente con los datos del usuario que está logueado."*

- Alertas y notificaciones ya son per-usuario tras T6.4.
- Sources y News siguen globales (B0/B3 vigentes).
- **Pendiente**: el frontend debe filtrar dashboard, wordcloud y stats por las alertas del usuario logueado (tarea **T4/T5**).

### CAMBIO #3 — La API debe cumplirse exactamente — ✅ Aplicado en Fase 1
- El profesor entregó el `main.py` oficial.
- **Operaciones y modelos NO se pueden cambiar.** Solo se pueden añadir endpoints auxiliares.
- Toda la API se ha realineado: prefijo `/api/v1`, schemas, modelos, endpoints anidados, tablas split, etc.

---

## 📋 Estado actual frente a los 40 checks del profesor

Leyenda: ✅ hecho · 🟡 parcial · ❌ pendiente

| # | Check | Estado | Notas |
|---|---|---|---|
| 1 | Alertas sobre palabra clave | ✅ | Funciona |
| 2 | Recomienda 3-10 sinónimos | ✅ | Recommender garantizado en Fase 0 (T9) |
| 3 | Límite 20 alertas/gestor | ✅ | `MAX_ALERTS = 20` verificado (T10) |
| 4 | Selección fuentes específicas | ✅ | `rss_channels_ids` + `information_sources_ids` (T6.4) |
| 5 | Categoría IPTC primer nivel | ✅ | `categories: List[{code, label}]` (T6.4) |
| 6 | Cron expression | ✅ | APScheduler + `CRAWLER_CRON_EXPRESSION` |
| 7 | Clasificación según alerta o fuente | ✅ | `resolve_news_classification` |
| 8 | Email al detectar match | ✅ | MailHog en dev |
| 9 | Mensaje al buzón interno | ✅ | NotificationDetailResponse |
| 10 | Título "Actualización de [alerta] en [día/hora]" | ✅ | Formato dd/mm/yyyy HH:MM |
| 11 | Resumen del RSS en notificación | ✅ | Body de notificación incluye summary |
| 12 | Alta de canales RSS asociados a un medio | ✅ | `/api/v1/information-sources/{id}/rss-channels` (T6.3) |
| 13 | Mínimo 100 canales | ✅ | 110 sembrados |
| 14 | ≥10 medios diferentes | ✅ | 20 medios |
| 15 | Canales para todas las cat IPTC | ✅ | 17 categorías cubiertas |
| 16 | Roles "Gestor" y "Lector" definidos | ✅ | Adenda lo redujo a gestor + admin |
| 17 | Lector bloqueado en alertas | ✅ | N/A por adenda |
| 18 | Email + nombre + apellidos + organización | ✅ | `organization` NOT NULL en T6.7 |
| 19 | Email de verificación | ✅ | Endpoint `/auth/verify-email` |
| 20 | Token expira a 24h | ✅ | `verification_token_expire_hours=24` |
| 21 | Admin inicial | ✅ | Seed en `_seed_admin_user` |
| 22 | Nubes palabras por categoría | ✅ | `/news/me/wordcloud` filtra solo noticias matcheadas (T5) |
| 23 | Nº total noticias en stats | ✅ | `/news/me/stats` per-user (T4) |
| 24 | Alertas por categoría | ✅ | `/alerts/me/stats` per-user, integrado en dashboard (T4) |
| 25 | i18n ES/EN | ✅ | react-i18next |
| 26 | API REST | ✅ | FastAPI |
| 27 | OpenAPI documentado | ✅ | Auto FastAPI; matchea oficial tras Fase 1 |
| 28 | GET /api/v1/health | ✅ | |
| 29 | Almacena noticias y entidades | ✅ | Postgres |
| 30 | Código en GitHub | ✅ | |
| 31 | Documentación Markdown | ✅ | |
| 32 | ADRs en `/docs/adr` | ✅ | Movido en Fase 2 (D1) |
| 33 | Diagramas de arquitectura | ✅ | `docs/diagrams/architecture.md`, `sequence-notification.md`, `deployment.md` (D2) |
| 34 | Pruebas automatizadas en CI | ✅ | CI corre 25 tests con cobertura (TS2 + TS3) |
| 35 | GitHub Actions para despliegue | 🟡 | CI sí, **CD no** (CD1) |
| 36 | Métricas calidad (SonarQube) | ❌ | (CD3) |
| 37 | Despliegue automático máquina limpia | 🟡 | `docker compose up` lo hace; documentar (CD2) |
| 38 | Informe cobertura automático | ✅ | `pytest-cov` integrado en CI; artefacto `backend-coverage` (TS3) |
| 39 | Trazabilidad requisitos-código | ❌ | (D4) |
| 40 | Registro de prompts IA | ❌ | (D5) |

**Resumen actual tras Fase 2: 36 ✅ · 2 🟡 · 2 ❌** (vs 30 ✅ · 7 🟡 · 3 ❌ antes de Fase 2; 22 ✅ · 11 🟡 · 7 ❌ antes de Fase 1).

---

## 🗂️ Tareas — estado y asignación

### ✅ Hechas en Fase 0 (Cristina)

| ID | Tarea | Notas |
|---|---|---|
| **T1** | Eliminar rol lector | Enum, default GESTOR, frontend, migración Alembic |
| **T6.1** | Prefijo `/api/v1` | Ya existía; verificado |
| **T6.2** | Role como entidad | Tabla roles + user_roles + endpoints CRUD + seed admin/gestor |
| **T7** | Atomicidad crawler | Verificado, sin cambios |
| **T9** | Recommender 3-10 | Garantizado con fallback genérico |
| **T10** | Límite 20 alertas/gestor | Verificado |
| **TS1** | Blindaje `conftest.py` | Aborta si BD no contiene "test"; CI ajustado |

### ✅ Hechas en Fase 1 (Cristina)

| ID | Tarea | Notas |
|---|---|---|
| **T6.3** | Sources split → Category + InformationSource + RSSChannel | Migración con backfill, IDs preservados |
| **T6.4** | Alerts oficial | descriptors, categories[], rss_channels_ids[], information_sources_ids[]; user_id; matching adaptado |
| **T6.5** | Notifications oficial | timestamp + metrics; endpoints anidados oficiales + atajos `/users/me` |
| **T6.6** | Stats endpoint | Módulo nuevo + tabla + CRUD oficial |
| **T6.7** | Users oficial | organization NOT NULL + sizes 120/180 + password min 6 + CRUD `/users` |
| **B0/B1/B2/B3** | Bugs sources/alertas/news/notif globales | Resueltos por el equipo antes de Fase 0/1 |

### ✅ Hechas en Fase 2 (Cristina)

| ID | Tarea | Notas |
|---|---|---|
| **T4** | Dashboard filtrado per-user | Endpoints `/news/me/stats`, `/news/me/wordcloud`, `/alerts/me/stats`. Frontend `DashboardPage` consume los `me/*` |
| **T5** | WordCloud solo con noticias matcheadas | Implementado vía subquery `news.id IN (SELECT news_id FROM notifications WHERE user_id=:me)` |
| **TS2** | Tests backend ampliados | `test_auth.py` (7 tests), `test_sources_split.py` (4), `test_alerts_per_user.py` (5) + helpers compartidos |
| **TS3** | Cobertura `pytest-cov` en CI | `pytest-cov` añadido + reportes XML/HTML como artefacto en GitHub Actions |
| **D1** | ADRs movidos a `/docs/adr` | `git mv docs/decisions docs/adr` + actualizadas referencias |
| **D2** | Diagramas arquitectura | Mermaid en `docs/diagrams/architecture.md`, `sequence-notification.md`, `deployment.md` |
| **D3** | Docs técnicas core | `architecture.md`, `api-design.md`, `database-design.md`, `extension-guide.md`, `testing-strategy.md` |
| **D6** | `.env.example` raíz + backend | Plantillas con comentarios, sin secretos |

### 🔴 Pendientes Fase 3 (única que queda)

| ID | Tarea | Responsable | Detalle | Cubre check |
|---|---|---|---|---|
| **TS4** | Smoke tests frontend (vitest) | **100475102** | Instalar vitest + 3 tests de páginas clave | (refuerza #34) |
| **TS5** | Tests crawler (success, error, dedup) | **100475101** | Mockear feedparser; 3 archivos test | (refuerza #34) |
| **CD1** | Pipeline despliegue (GitHub Actions) | **Javier** | Build + push imágenes a `ghcr.io` en push a main | #35 |
| **CD2** | Documentar despliegue máquina limpia | **Javier** | Sección en `docs/deployment.md` | #37 |
| **CD3** | SonarCloud o métricas calidad | **Javier** | Action Sonar o `ruff/eslint` como artefactos | #36 |
| **D4** | Trazabilidad requisitos-código | **Cristina** | Tabla en `docs/traceability.md` | #39 |
| **D5** | Registro de prompts IA | **Cristina** | `docs/ai-prompts.md` | #40 |

### Tareas obsoletas

#### Absorbidas por Fase 1

| ID original | Por qué ya no aplica |
|---|---|
| T2 (revertir alertas a per-user) | Absorbida en T6.4 |
| T3 (revertir notificaciones a creador) | Absorbida en T6.5 |
| T8 (organization obligatoria) | Absorbida en T6.7 |
| T21 (ocultar acciones a lector) | El rol lector se eliminó (CAMBIO #1) |
| T22 (script demo reproducible) | Ya existe `docs/demo.md` |

---

## 🔧 Mapa final de endpoints alineados con la API oficial

### Endpoints oficiales (idénticos a `main.py` del aula global)

```
POST   /api/v1/auth/login
POST   /api/v1/auth/register
GET    /api/v1/health

GET    /api/v1/users                                 (lista)
POST   /api/v1/users                                 (admin only, 201)
GET    /api/v1/users/{user_id}
PUT    /api/v1/users/{user_id}
DELETE /api/v1/users/{user_id}                       (204)

GET/POST/GET/PUT/DELETE  /api/v1/roles[/{id}]
GET/POST/GET/PUT/DELETE  /api/v1/categories[/{id}]
GET/POST/GET/PUT/DELETE  /api/v1/information-sources[/{id}]
GET/POST/GET/PUT/DELETE  /api/v1/information-sources/{id}/rss-channels[/{cid}]

GET/POST/GET/PUT/DELETE  /api/v1/users/{user_id}/alerts[/{alert_id}]
GET/POST/GET/PUT/DELETE  /api/v1/users/{user_id}/alerts/{alert_id}/notifications[/{nid}]

GET/POST/GET/PUT/DELETE  /api/v1/stats[/{id}]
```

### Endpoints añadidos sobre el contrato (permitido por el profesor)

```
GET    /api/v1/users/me/alerts                       (atajo)
POST   /api/v1/users/me/alerts                       (atajo)
GET    /api/v1/users/me/notifications                (bandeja UI)
GET    /api/v1/users/me/notifications/{id}/details
PATCH  /api/v1/users/me/notifications/{id}/read|unread
DELETE /api/v1/users/me/notifications/{id}
PATCH  /api/v1/users/{u}/alerts/{a}/activate|deactivate
PATCH  /api/v1/information-sources/{s}/rss-channels/{c}/activate|deactivate
GET    /api/v1/alerts/categories                     (lista IPTC)
GET    /api/v1/alerts/suggestions/{keyword}          (recommender 3-10)
GET    /api/v1/alerts/me/stats                       (dashboard per-user)
GET    /api/v1/information-sources/catalog/summary   (checklist #13-15)
GET    /api/v1/news/...                              (no oficial, permitido)
GET    /api/v1/auth/verify-email
POST   /api/v1/auth/resend-verification
GET    /api/v1/auth/users
PATCH  /api/v1/auth/users/{id}/role                  (CAMBIO #1)
GET    /api/v1/health/db
```

---

## 🗄️ Migraciones Alembic aplicadas (en orden)

1. `f1a2b3c4d5e6` — Roles entity + remove lector (Fase 0)
2. `f2b3c4d5e6f7` — Split sources → categories + information_sources + rss_channels (T6.3)
3. `f3c4d5e6f7a8` — Align alerts with official API (T6.4)
4. `f4d5e6f7a8b9` — Align notifications with official API (T6.5)
5. `f5e6f7a8b9c0` — Create stats table (T6.6)
6. `f6f7a8b9c0d1` — Align users with official API (T6.7)

Verificado: arrancando Docker desde cero las 6 migraciones aplican limpio, se siembran 110 canales en 20 medios y los 9/9 tests pasan contra `newsradar_test`.

---

## 📅 Orden de merge sugerido para cerrar el proyecto

### ✅ Sprint A — Fase 2 (cerrada en `feature/phase2-cristina`)
- T4, T5, TS2, TS3, D1, D2, D3, D6 — todo merged en una sola rama.

### Sprint B — Fase 3 (~2-3 días, en paralelo)
- **100475102** → TS4 (vitest frontend)
- **100475101** → TS5 (tests crawler)
- **Javier** → CD1, CD2, CD3 (CD pipeline + deployment doc + Sonar)
- **Cristina** → D4, D5 (trazabilidad, prompts IA)

### Sprint C — Cierre (1 día)
- Smoke test conjunto: `docker compose up --build` desde rama main, recorrer `docs/demo.md`.
- Verificar 40/40 checks del checklist del profesor.
- Crear release tag.

---

## 📐 Reglas de trabajo

- Una rama por persona-tarea: `feature/<nombre>-<id>` (ej. `feature/manso-T4-dashboard-per-user`).
- PR a `main` con descripción: tarea cerrada, checklist del profesor cubierto, captura/curl de verificación.
- Review mínima de 1 compañero antes de mergear.
- Cada commit con tu cuenta de la uni (Phase 0 ya configuró el local).
- No push directo a `main`.

---

## 📌 Estado final esperado (cuando se cierre Sprint C)

- 40/40 checks del `DOSS-CHECKLIST_2026` ✅
- 26/26 checks de proceso general ✅
- API matchea exactamente la oficial del aula global ✅
- CI + CD verde ✅
- Cobertura > 60% ✅
- Documentación completa (ADRs, diagramas, traceability, prompts IA) ✅
- Demo reproducible documentada ✅
