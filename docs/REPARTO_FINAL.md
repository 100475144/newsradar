# Reparto de tareas finales — NEWSRADAR

**Última actualización:** 23 mayo 2026 — sistema cierra con **278 OK + 1 WARNING admitido + 2 NOK admitidos = 99.29 % efectivo** sobre 281 casos en la batería oficial (`devops_verifica`, versión del 20/05/2026).

Este documento se cruza con:
- `DOSS-CHECKLIST_2026` (40 checks de proyecto + 26 de proceso)
- Adenda oficial: desaparece el rol "lector" (CAMBIO #1)
- Adenda oficial: registro automático con rol gestor (CAMBIO #1bis)
- Dudas 21-abr y 28-abr (CAMBIO #2: dashboards per-user)
- Correo 29-abr + `main.py` oficial del aula global (CAMBIO #3)

Reglas de trabajo: rama `feature/<nombre>-<tema>`, PR a `main` con review mínima de 1 compañero, **CI verde antes de mergear**, sin push directo a `main`.

---

## ✅ Estado global de las fases (todas mergeadas a `main`)

| Fase | Contenido | Estado | PR |
|---|---|---|---|
| **Fase 0** | Adendas CAMBIO #1/#1bis + verificaciones (T1, T6.1, T6.2, T7, T9, T10, TS1) | ✅ Mergeada | #10/#11 |
| **Fase 1** | Refactor masivo CAMBIO #3 (T6.3, T6.4, T6.5, T6.6, T6.7) | ✅ Mergeada | #11 |
| **Fase 2** | Dashboard per-user + tests + cobertura + ADRs + diagramas + docs (T4, T5, TS2, TS3, D1-D3, D6) | ✅ Mergeada | #11 |
| **Fase 3** | Tests frontend + crawler + trazabilidad + prompts IA (TS4, TS5, D4, D5) | ✅ Mergeada | #12 |
| **Fixes CI** | SMTP en CI + `localStorage` en setup vitest + assert robusto crawler | ✅ Mergeada | #13 |
| **CDx** | CD pipeline + SonarQube + deployment doc | 🔴 Pendiente | — |

---

## 📢 Cambios oficiales sobre el enunciado (todos cubiertos)

### CAMBIO #1 — Desaparece el rol "lector" — ✅ Aplicado
- Solo existen `gestor` y `admin` (= gestor inicial).
- El **API mantiene** los endpoints de creación y asignación de roles.
- Todas las restricciones UX por `role == "lector"` eliminadas.

### CAMBIO #1bis — Asignación automática de rol "gestor" — ✅ Aplicado
> *"Todo nuevo usuario tendrá el rol de 'gestor' automáticamente. Eso sí, el rol de 'admin' debe existir."*

- El registro nunca acepta `role` ni `role_ids` en el body.
- El servidor asigna `gestor` automáticamente vía `role_ids`.
- El rol `admin` se conserva (seed inicial + endpoints admin).

### CAMBIO #2 — Dashboard/WordCloud/Stats per-user — ✅ Aplicado
> *"La información se genera solamente con los datos del usuario que está logueado."*

- Alertas y notificaciones son per-usuario.
- `/news/me/stats`, `/news/me/wordcloud`, `/alerts/me/stats` filtran por las alertas del user logueado vía subquery sobre `notifications`.
- Sources y News siguen globales (visibles para todos).

### CAMBIO #3 — La API matchea exactamente la oficial — ✅ Aplicado
- El profesor entregó el `main.py` oficial.
- **Operaciones y modelos NO se cambian.** Solo se añaden endpoints auxiliares.
- Toda la API realineada: prefijo `/api/v1`, schemas, modelos, endpoints anidados, tablas split.

---

## 📋 Estado actual frente a los 40 checks del profesor

Leyenda: ✅ hecho · 🟡 parcial · ❌ pendiente

| # | Check | Estado | Notas |
|---|---|---|---|
| 1 | Alertas sobre palabra clave | ✅ | `/users/{u}/alerts` con `descriptors` |
| 2 | Recomienda 3-10 sinónimos | ✅ | Recommender garantizado con fallback genérico |
| 3 | Límite 20 alertas/gestor | ✅ | `MAX_ALERTS = 20` + test `test_alert_max_limit_per_gestor` |
| 4 | Selección fuentes específicas | ✅ | `rss_channels_ids` + `information_sources_ids` |
| 5 | Categoría IPTC primer nivel | ✅ | `categories: List[{code, label}]` |
| 6 | Cron expression | ✅ | APScheduler + `CRAWLER_CRON_EXPRESSION` |
| 7 | Clasificación según alerta o fuente | ✅ | `_resolve_news_classification` + tests |
| 8 | Email al detectar match | ✅ | MailHog en dev + test E2E |
| 9 | Mensaje al buzón interno | ✅ | `NotificationDetailResponse` |
| 10 | Título "Actualización de [alerta] en [día/hora]" | ✅ | Formato dd/mm/yyyy HH:MM |
| 11 | Resumen del RSS en notificación | ✅ | Body de notificación incluye summary |
| 12 | Alta de canales RSS asociados a un medio | ✅ | `/information-sources/{id}/rss-channels` |
| 13 | Mínimo 100 canales | ✅ | 110 sembrados |
| 14 | ≥10 medios diferentes | ✅ | 20 medios |
| 15 | Canales para todas las cat IPTC | ✅ | 17 categorías cubiertas |
| 16 | Roles "Gestor" y "Lector" definidos | ✅ | Adenda lo redujo a gestor + admin |
| 17 | Lector bloqueado en alertas | ✅ | N/A por adenda |
| 18 | Email + nombre + apellidos + organización | ✅ | `organization` NOT NULL |
| 19 | Email de verificación | ✅ | Endpoint `/auth/verify-email` |
| 20 | Token expira a 24h | ✅ | `verification_token_expire_hours=24` |
| 21 | Admin inicial | ✅ | `_seed_admin_user` en arranque |
| 22 | Nubes palabras por categoría | ✅ | `/news/me/wordcloud` per-user |
| 23 | Nº total noticias en stats | ✅ | `/news/me/stats` per-user |
| 24 | Alertas por categoría | ✅ | `/alerts/me/stats` per-user |
| 25 | i18n ES/EN | ✅ | react-i18next con detector |
| 26 | API REST | ✅ | FastAPI |
| 27 | OpenAPI documentado | ✅ | Auto-generado en `/docs` |
| 28 | GET /api/v1/health | ✅ | |
| 29 | Almacena noticias y entidades | ✅ | Postgres con 12 tablas |
| 30 | Código en GitHub | ✅ | https://github.com/100475144/newsradar |
| 31 | Documentación Markdown | ✅ | 9 docs + 3 diagramas Mermaid |
| 32 | ADRs en `/docs/adr` | ✅ | Movidos en Fase 2 |
| 33 | Diagramas de arquitectura | ✅ | architecture, sequence-notification, deployment |
| 34 | Pruebas automatizadas en CI | ✅ | 31 tests backend + 7 frontend |
| 35 | GitHub Actions para despliegue | 🟡 | CI sí, **CD no** (CD1) |
| 36 | Métricas calidad (SonarQube) | ❌ | (CD3) |
| 37 | Despliegue automático máquina limpia | 🟡 | `docker compose up` lo hace, falta documentar (CD2) |
| 38 | Informe cobertura automático | ✅ | pytest-cov + artefacto `backend-coverage` |
| 39 | Trazabilidad requisitos-código | ✅ | `docs/traceability.md` |
| 40 | Registro de prompts IA | ✅ | `docs/ai-prompts.md` |

**Resumen actual: 38 ✅ · 2 🟡 · 1 ❌** (#36 estricto)

(Histórico: 22 ✅ pre-Fase 1 → 30 ✅ tras Fase 1 → 36 ✅ tras Fase 2 → **38 ✅ tras Fase 3 + fixes CI**)

Tras los 3 CDx asignados a Javier, el proyecto llegará a **40/40 ✅**.

---

## 🗂️ Histórico de tareas hechas

### ✅ Fase 0 (Cristina)

| ID | Tarea | Notas |
|---|---|---|
| **T1** | Eliminar rol lector | Enum + default GESTOR + frontend + migración Alembic |
| **T6.1** | Prefijo `/api/v1` | Verificado |
| **T6.2** | Role como entidad | Tabla roles + user_roles + endpoints CRUD + seed admin/gestor |
| **T7** | Atomicidad crawler | Verificado |
| **T9** | Recommender 3-10 | Garantizado con fallback genérico |
| **T10** | Límite 20 alertas/gestor | Verificado |
| **TS1** | Blindaje `conftest.py` | Aborta si BD no contiene "test" |

### ✅ Fase 1 (Cristina)

| ID | Tarea | Notas |
|---|---|---|
| **T6.3** | Sources split | Category + InformationSource + RSSChannel; migración con backfill, IDs preservados |
| **T6.4** | Alerts oficial | descriptors, categories[], rss_channels_ids[], information_sources_ids[]; matching adaptado |
| **T6.5** | Notifications oficial | timestamp + metrics; endpoints anidados + atajos `/users/me` |
| **T6.6** | Stats endpoint | Módulo nuevo + tabla + CRUD oficial |
| **T6.7** | Users oficial | organization NOT NULL + sizes 120/180 + password ≥6 + CRUD `/users` |
| **B0/B1/B2/B3** | Bugs sources/alertas/news/notif globales | Resueltos por el equipo antes de Fase 0/1 |

### ✅ Fase 2 (Cristina)

| ID | Tarea | Notas |
|---|---|---|
| **T4** | Dashboard per-user | `/news/me/stats`, `/news/me/wordcloud`, `/alerts/me/stats` |
| **T5** | WordCloud filtrado | Subquery `news.id IN (SELECT news_id FROM notifications WHERE user_id=:me)` |
| **TS2** | Tests backend ampliados | 16 tests (auth + sources_split + alerts_per_user) + helpers compartidos |
| **TS3** | Cobertura `pytest-cov` en CI | XML + HTML como artefacto |
| **D1** | ADRs movidos a `/docs/adr` | Reorganización |
| **D2** | Diagramas arquitectura | 3 diagramas Mermaid (bloques, secuencia, despliegue) |
| **D3** | Docs técnicas core | architecture, api-design, database-design, extension-guide, testing-strategy |
| **D6** | `.env.example` raíz + backend | Plantillas con comentarios |

### ✅ Fase 3 (Cristina)

| ID | Tarea | Notas |
|---|---|---|
| **TS4** | Smoke tests frontend con vitest | 7 tests: LoginPage (3), AlertsPage (2), NewsPage (2) + setup con mocks |
| **TS5** | Tests crawler | 6 tests: success, empty, malformed, broken, dedup, only-active |
| **D4** | Trazabilidad requisitos↔código↔tests | `docs/traceability.md` |
| **D5** | Registro de prompts IA | `docs/ai-prompts.md` por fase |

### ✅ Fixes CI (Cristina)

| Fix | Notas |
|---|---|
| `4d40273` | Vars SMTP en `backend-test` job (test E2E necesita MailHog accesible) |
| `c55c39c` | Tests vitest: `queryAllByText` en LoginPage; `<input>` en NewsPage |
| `4e3f630` | Mock `localStorage`/`sessionStorage` en `setup.js` (jsdom no siempre los expone) |
| `b480125` | Test crawler `active-only` con asserts de pertenencia (resiliente a seeds) |

### 🔴 Pendientes — CDx (Javier)

| ID | Tarea | Detalle | Cubre check |
|---|---|---|---|
| **CD1** | Pipeline despliegue (GitHub Actions) | Build + push imágenes a `ghcr.io` en push a main | #35 |
| **CD2** | Documentar despliegue máquina limpia | Sección en `docs/deployment.md` paso a paso | #37 |
| **CD3** | SonarCloud o métricas calidad | Action Sonar o `ruff/eslint` como artefactos con badge | #36 |

### Tareas obsoletas (absorbidas)

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

GET/POST/PUT/DELETE  /api/v1/roles[/{id}]
GET/POST/PUT/DELETE  /api/v1/categories[/{id}]
GET/POST/PUT/DELETE  /api/v1/information-sources[/{id}]
GET/POST/PUT/DELETE  /api/v1/information-sources/{id}/rss-channels[/{cid}]

GET/POST/PUT/DELETE  /api/v1/users/{user_id}/alerts[/{alert_id}]
GET/POST/PUT/DELETE  /api/v1/users/{user_id}/alerts/{alert_id}/notifications[/{nid}]

GET/POST/PUT/DELETE  /api/v1/stats[/{id}]
```

### Endpoints añadidos (permitidos por el profesor)

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
GET    /api/v1/news/...                              (no oficial, permitido)
GET    /api/v1/news/me/stats                         (per-user)
GET    /api/v1/news/me/wordcloud                     (per-user)
GET    /api/v1/information-sources/catalog/summary   (checklist #13-15)
POST   /api/v1/crawler/run                           (disparo manual)
GET    /api/v1/auth/verify-email
POST   /api/v1/auth/resend-verification
GET    /api/v1/auth/users
PATCH  /api/v1/auth/users/{id}/role                  (CAMBIO #1)
GET    /api/v1/health/db
```

---

## 🗄️ Migraciones Alembic aplicadas (en orden)

Las 6 migraciones de Fase 0/1 + las anteriores del equipo se aplican limpio desde cero. Lista completa en [`docs/database-design.md`](database-design.md).

Hitos:
1. `f1a2b3c4d5e6` — Roles entity + remove lector (Fase 0)
2. `f2b3c4d5e6f7` — Split sources → categories + information_sources + rss_channels (T6.3)
3. `f3c4d5e6f7a8` — Align alerts with official API (T6.4)
4. `f4d5e6f7a8b9` — Align notifications with official API (T6.5)
5. `f5e6f7a8b9c0` — Create stats table (T6.6)
6. `f6f7a8b9c0d1` — Align users with official API (T6.7)

Verificado: 110 canales en 20 medios sembrados al arrancar, 31/31 tests pasan contra `newsradar_test` con cobertura 75%.

---

## 📅 Plan para cierre del proyecto

### ✅ Hecho (mergeado a main)
Fases 0+1+2+3 + fixes CI.

### 🔴 Sprint final — CDx (Javier, 1-2 días)
- **CD1** Pipeline despliegue: `cd.yml` con build + push a `ghcr.io` en push a `main`
- **CD2** Documentar despliegue máquina limpia: añadir sección en `docs/deployment.md` con receta paso a paso (clonar → `.env` → up → smoke health)
- **CD3** SonarCloud action o badges de ruff/eslint en README

### 🎯 Cierre (cuando estén los 3 CDx)
- Smoke test conjunto: `docker compose up --build` desde `main`, recorrer `docs/demo.md`
- Verificar **40/40** checks del checklist del profesor
- Crear release tag `v1.0.0`

---

## 🧪 Verificación oficial (`devops_verifica`, versión del 20/05/2026)

Última ejecución 23 mayo 2026 — **99.29 % efectivo** sobre 281 casos.

| Tipo | Casos |
|---|---|
| OK | 278 |
| WARNING (admitido por el profesor) | 1 (`GA-011`) |
| NOK admitido por el profesor | 2 (`GC-009`, `GC-010`) |

El profesor publicó el 20/05/2026 una versión actualizada de la batería que:

* Resuelve **`SMOKE-005`** directamente en el verificador (función
  `_extract_iptc_code` corregida para aceptar tanto string como entero en
  el campo `id`).
* **Comenta `GC-008`** porque el payload generado no permitía la aserción
  esperada — quedan ahora 281 casos totales en lugar de 282.

Los 2 NOK que mantenemos están **admitidos explícitamente por el profesor**
en su correo del 14/05/2026: el `POST /categories` es idempotente sobre el
catálogo cerrado IPTC (devuelve 201 con la fila canónica en vez de 409).
El WARNING de `GA-011` también está admitido (auto-relleno de descriptors
para garantizar el rango 3-10 del enunciado).

Decisiones documentadas en:
- `docs/adr/category_iptc_contract.md` — `Category.id` entero, POST idempotente, validación `code`.
- `docs/adr/url_validation.md` — política DNS + HEAD rápido para evitar acoplar latencia del POST a infraestructura externa.
- `docs/adr/alert_descriptors.md` — auto-relleno de `descriptors` para garantizar 3-10 elementos.

---

## 📌 Checklist de "perfección" antes de la entrega

Para llegar literalmente a 40/40 ✅ y maximizar nota:

- [ ] **CD1**, **CD2**, **CD3** mergeados (Javier)
- [ ] Limpieza repo: borrar `backend;C/` (artefacto Windows) y `package-lock.json` raíz
- [ ] Actualizar `docs/demo.md` con paso "verifica dashboard per-user"
- [ ] Añadir 2-3 screenshots en `docs/images/`
- [ ] Tag `v1.0.0` y release notes en GitHub

Las 4 últimas son cosméticas — sin ellas el proyecto sigue siendo entregable.
