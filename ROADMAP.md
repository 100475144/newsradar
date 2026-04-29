# NEWSRADAR — Roadmap

> Plan de sprints y fases del proyecto. Para el estado vivo de tareas
> concretas y reparto por persona, ver [`docs/REPARTO_FINAL.md`](docs/REPARTO_FINAL.md).

---

## Estado de los sprints

| Sprint       | Objetivo                                  | Estado          |
| ------------ | ----------------------------------------- |-----------------|
| Sprint 0     | Preparación de infraestructura            | ✅ Completado    |
| Sprint 1     | Usuarios y autenticación                  | ✅ Completado    |
| Sprint 2     | Gestión de fuentes RSS                    | ✅ Completado    |
| Sprint 3     | Gestión de alertas                        | ✅ Completado    |
| Sprint 4     | Monitorización de noticias (crawler)      | ✅ Completado    |
| Sprint 5     | Notificaciones + API REST                 | ✅ Completado    |
| Sprint 6     | Dashboard y visualización                 | ✅ Completado    |
| Sprint 7     | Testing, CI/CD y calidad                  | 🟡 Parcial — CD pendiente (CD1, CD2, CD3) |
| Sprint 8     | Documentación                             | ✅ Completado    |
| **Fase 0**   | Adenda oficial CAMBIO #1/#1bis            | ✅ Completado    |
| **Fase 1**   | Refactor masivo CAMBIO #3 (`main.py` oficial) | ✅ Completado |
| **Fase 2**   | Dashboard per-user + ampliación tests + docs técnicas | ✅ Completado |
| **Fase 3**   | Tests frontend + crawler + trazabilidad + prompts IA | ✅ Completado (sin CDx) |

---

## Roles del equipo

| Rol | Persona | Foco principal |
|---|---|---|
| **P1** | Cristina (100475144) | Arquitectura backend + Auth + Documentación + alineación API oficial |
| **P2** | Manso (100474286) | Sources + Frontend UX + Dashboard |
| **P3** | 100475101 | News + Crawler + Scheduler |
| **P4** | 100475102 | Alerts + Matching + Notifications |
| **P5** | Manso (100474286) | Frontend |
| **P6** | Adrian (100495924) | Infraestructura + DB + Testing + CI |
| **(extra)** | Javier Martín | CI/CD transversal + reviews |

---

## Sprints originales (resumen)

### Sprint 0 — Infraestructura

Dejar el proyecto listo para que todos puedan empezar a programar.

- Docker Compose con backend + frontend + Postgres
- FastAPI app esqueleto con endpoint `/health`
- React + Vite arrancando y consumiendo `/health`
- Estructura modular de los 6 módulos backend (auth, sources, news, crawler, alerts, notifications)

### Sprint 1 — Auth y usuarios

- Modelo `User`, registro, login, JWT, endpoint `/me`
- Verificación de email con token de 24 h
- Roles `admin` y `gestor` (rol `lector` retirado por adenda)
- UI de login y registro
- Migraciones Alembic de `users` y `roles`

### Sprint 2 — Gestión de fuentes RSS

- CRUD de canales RSS asociados a un medio
- Validación de URL y categoría IPTC
- UI completa para listar/crear/editar/borrar fuentes
- Catálogo inicial sembrado: 110 canales en 20 medios cubriendo las 17 categorías IPTC

### Sprint 3 — Gestión de alertas

- Modelo `Alert` con descriptors, categorías, filtros por canal/medio, cron
- CRUD completo + activar/desactivar
- Recommender de descriptors (3-10 sinónimos por keyword)
- Límite 20 alertas por gestor

### Sprint 4 — Crawler

- Cliente RSS con feedparser
- Scheduler con APScheduler y cron expression configurable
- Deduplicación por external_id, link y content_hash
- Persistencia en tabla `news`

### Sprint 5 — Notificaciones + API

- Motor de matching que clasifica y dispara notificaciones
- Notificaciones in-app + email (SMTP via MailHog en dev)
- Dedupe por `(user_id, alert_id, news_id)`
- Endpoints anidados oficiales `/users/{u}/alerts/{a}/notifications`

### Sprint 6 — Dashboard

- Dashboard con stats globales y per-user
- Wordcloud calculada con las noticias matcheadas por las alertas del usuario
- i18n ES/EN con detector automático

### Sprint 7 — Testing y CI

- pytest + pytest-cov (~75% cobertura backend)
- vitest para frontend (smoke tests de páginas clave)
- GitHub Actions (CI: `backend-test`, `backend-lint`, `frontend-build`, `frontend-test`)
- Conftest blindado contra BD producción
- 🟡 **Pendiente:** CD pipeline + SonarQube + doc despliegue máquina limpia (asignados a Javier)

### Sprint 8 — Documentación

- `docs/architecture.md`, `api-design.md`, `database-design.md`, `extension-guide.md`, `testing-strategy.md`
- 3 diagramas Mermaid en `docs/diagrams/`
- ADRs en `docs/adr/`
- `docs/demo.md` reproducible
- Trazabilidad requisitos↔código↔tests
- Registro de prompts IA

---

## Fases de cierre (post-adendas oficiales)

A mitad del proyecto el profesor publicó adendas y dudas que obligaron a un refactor masivo. Para gestionarlo, se ejecutaron 4 fases de cierre adicionales:

### Fase 0 — Cumplir adendas CAMBIO #1 y #1bis

- T1: eliminar rol `lector`
- T6.1/T6.2: prefijo `/api/v1` y `Role` como entidad propia
- T7/T9/T10: verificaciones de atomicidad crawler, recommender 3-10, límite 20 alertas
- TS1: blindaje conftest

### Fase 1 — Alinear API con `main.py` oficial (CAMBIO #3)

| Sub-tarea | Cambio |
|---|---|
| T6.3 | Sources split → `Category` + `InformationSource` + `RSSChannel` |
| T6.4 | Alerts oficial: `descriptors`, `categories[]`, `rss_channels_ids[]`, `information_sources_ids[]` |
| T6.5 | Notifications con `timestamp + metrics` |
| T6.6 | Stats endpoint nuevo |
| T6.7 | User: `organization` obligatoria + tamaños 120/180 + CRUD oficial |

6 migraciones Alembic con backfill, sin pérdida de datos.

### Fase 2 — Dashboard per-user + tests + docs

- T4/T5: dashboards filtrados por las alertas del user logueado (CAMBIO #2)
- TS2: +16 tests backend con helpers compartidos
- TS3: pytest-cov en CI con artefactos
- D1: ADRs movidos a `docs/adr`
- D2: 3 diagramas Mermaid
- D3: 5 documentos técnicos
- D6: `.env.example` raíz + backend

### Fase 3 — Cierre (sin CDx)

- TS4: vitest + 7 smoke tests frontend
- TS5: 6 tests crawler con feedparser mockeado
- D4: trazabilidad completa de los 40 checks
- D5: registro de prompts IA por fase

---

## Verificación final

Flujo completo end-to-end probado:

1. ✅ Registro de usuario (organization obligatoria)
2. ✅ Verificación de email (24h, vía MailHog en dev)
3. ✅ Login (JWT, role_ids: [2] = gestor)
4. ✅ Crear alerta (schema oficial: descriptors, categories[], cron)
5. ✅ Crawler ejecuta cron `*/5 * * * *` y captura news
6. ✅ Backfill matching: la alerta nueva genera notificaciones para news pre-existentes
7. ✅ Notificación in-app + email entregado en MailHog
8. ✅ Dashboard del user muestra solo SUS noticias y categorías
9. ✅ `/news/me/wordcloud` solo con palabras de news matcheadas

---

## Lo que queda para la entrega final (40/40 ✅)

| ID | Tarea | Responsable |
|---|---|---|
| **CD1** | Pipeline despliegue (build + push imágenes a `ghcr.io`) | Javier |
| **CD2** | Documentar despliegue máquina limpia en `docs/deployment.md` | Javier |
| **CD3** | SonarCloud / métricas calidad | Javier |

Ver detalle vivo en [`docs/REPARTO_FINAL.md`](docs/REPARTO_FINAL.md).
