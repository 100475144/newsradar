# NEWSRADAR

[![CI](https://github.com/100475144/newsradar/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/100475144/newsradar/actions/workflows/ci.yml)

NEWSRADAR es un **sistema modular de monitorización de noticias** que recoge artículos de feeds RSS y avisa a los usuarios cuando aparece contenido relevante para sus alertas. Proyecto académico de la asignatura de DevOps de la UC3M (curso 2025-2026).

El sistema permite registrar canales RSS asociados a medios de comunicación, definir alertas con palabras clave y filtros por canal/medio/categoría IPTC, y recibir notificaciones por correo electrónico y bandeja in-app cuando llegan noticias coincidentes.

---

## Visión rápida

- **Frontend:** React 19 + Vite + react-i18next + Recharts (ES/EN)
- **Backend API:** FastAPI + SQLAlchemy 2 + Alembic + APScheduler (Python 3.11)
- **Base de datos:** PostgreSQL 18 con JSONB para campos flexibles
- **Crawler:** APScheduler con cron configurable + feedparser
- **Email:** SMTP (MailHog en desarrollo)
- **Orquestación:** Docker Compose para todo el stack

La API se sirve bajo `/api/v1` y matchea exactamente la especificación oficial entregada por el profesor (`main.py` del aula global).

---

## Arquitectura

```text
                    ┌────────────────────┐
                    │  React + Vite UI   │  :5173
                    └─────────┬──────────┘
                              │  /api/v1/*  (JWT)
                    ┌─────────▼──────────┐
                    │  FastAPI Backend   │  :8000
                    │  - auth, users     │
                    │  - sources split   │
                    │  - alerts          │
                    │  - news + crawler  │
                    │  - notifications   │
                    │  - stats           │
                    └─┬────────────┬─────┘
                      │            │
                ┌─────▼─────┐  ┌───▼────────┐
                │ Postgres  │  │  MailHog   │  :8025 UI
                │   :5432   │  │  SMTP 1025 │
                └───────────┘  └────────────┘
                      ▲
                      │  feedparser HTTPS
                ┌─────┴─────┐
                │  Internet │
                └───────────┘
```

Diagramas detallados (bloques, secuencia, despliegue) en [`docs/diagrams/`](docs/diagrams/).

---

## Cómo arrancar

### Prerrequisitos
- Docker Desktop (con `docker compose`)
- Git

### Pasos

```bash
git clone https://github.com/100475144/newsradar.git
cd newsradar
cp .env.example .env          # ajusta valores si lo necesitas
docker compose up --build
```

Servicios disponibles:

| Servicio | URL | Notas |
|---|---|---|
| Frontend | http://localhost:5173 | React + Vite en modo dev |
| API | http://localhost:8000/api/v1/health | FastAPI con auto-reload |
| Swagger | http://localhost:8000/docs | OpenAPI auto-generado |
| MailHog | http://localhost:8025 | Bandeja de emails capturados |
| Postgres | localhost:5432 | usuario `user` / password `password` |

Al arrancar por primera vez:
- Se ejecutan automáticamente las **migraciones Alembic** (20+).
- Se crea el **usuario admin** (`admin@newsradar.com` / `Admin1234!`).
- Se siembra el **catálogo RSS por defecto** (110 canales en 20 medios cubriendo las 17 categorías IPTC).
- El **scheduler del crawler** arranca con cron `*/5 * * * *`.

> El primer login con el admin permite gestionar todo. Para crear gestores adicionales: registro normal en la UI + verificación de email vía MailHog (en dev) o el endpoint `/auth/verify-email`.

Para el flujo completo de demo, ver [`docs/demo.md`](docs/demo.md).

---

## Estructura del repo

```
newsradar/
├── backend/                       FastAPI app + Alembic migrations + tests
│   ├── app/
│   │   ├── api/                   routers globales y deps
│   │   ├── core/                  config, db, IPTC, seed sources, security, logging
│   │   ├── modules/               módulos de dominio (auth, sources, alerts, ...)
│   │   ├── alembic/               migraciones de la BD
│   │   └── tests/                 pytest
│   ├── pytest.ini
│   ├── ruff.toml
│   └── requirements.txt
├── frontend/                      React 19 + Vite
│   ├── src/
│   │   ├── api/                   clientes HTTP por módulo
│   │   ├── pages/                 páginas + tests vitest
│   │   ├── components/, context/, i18n/
│   │   └── test/                  setup vitest
│   ├── vite.config.ts
│   └── vitest.config.js
├── docs/                          documentación técnica (ver más abajo)
├── scripts/                       utilidades de desarrollo
├── .github/workflows/             CI (ci.yml)
├── docker-compose.yaml
├── docker-compose.test.yaml
├── .env.example                   plantilla de variables de entorno
└── README.md
```

---

## Documentación

Toda la documentación viva está en [`docs/`](docs/):

| Documento | Contenido |
|---|---|
| [`docs/architecture.md`](docs/architecture.md) | Capas, módulos, decisiones de diseño y flujos clave |
| [`docs/api-design.md`](docs/api-design.md) | Endpoints REST + traza con la API oficial del aula global |
| [`docs/database-design.md`](docs/database-design.md) | Modelo entidad-relación + descripción de tablas + migraciones |
| [`docs/extension-guide.md`](docs/extension-guide.md) | Cómo añadir módulo, canal RSS, categoría IPTC, endpoint, test, métrica |
| [`docs/testing-strategy.md`](docs/testing-strategy.md) | Niveles de test, comandos, fixtures, helpers, cobertura |
| [`docs/deployment.md`](docs/deployment.md) | Detalles de despliegue con Docker Compose |
| [`docs/demo.md`](docs/demo.md) | Script paso a paso para demostración funcional |
| [`docs/REPARTO_FINAL.md`](docs/REPARTO_FINAL.md) | Estado vivo del proyecto y reparto de tareas |
| [`docs/traceability.md`](docs/traceability.md) | Trazabilidad requisitos ↔ código ↔ tests (40 checks) |
| [`docs/ai-prompts.md`](docs/ai-prompts.md) | Registro de prompts de IA usados durante el desarrollo |
| [`docs/diagrams/`](docs/diagrams/) | Diagramas Mermaid: bloques, secuencia, despliegue |
| [`docs/adr/`](docs/adr/) | Architecture Decision Records |

---

## Tests

| Suite | Comando | Tests |
|---|---|---|
| Backend (pytest + cov) | `cd backend && pytest app/tests` | 31 tests, cobertura ~75% |
| Frontend (vitest) | `cd frontend && npm test` | 7 smoke tests |
| Linter | `ruff check backend/app/` | 0 errores |

Ver [`docs/testing-strategy.md`](docs/testing-strategy.md) para detalles.

El CI (GitHub Actions) corre las 4 jobs en cada PR a `main`: `backend-test`, `backend-lint`, `frontend-build`, `frontend-test`.

---

## API

La API completa se sirve bajo `/api/v1` y matchea estructuralmente la especificación oficial. Operaciones principales:

```
POST   /api/v1/auth/login                                            login + JWT
POST   /api/v1/auth/register                                         registro (rol gestor automático)
GET    /api/v1/health                                                healthcheck

GET/POST/PUT/DELETE  /api/v1/users[/{id}]                            CRUD users (admin only para POST/DELETE)
GET/POST/PUT/DELETE  /api/v1/roles[/{id}]                            CRUD roles
GET/POST/PUT/DELETE  /api/v1/categories[/{id}]                       CRUD categories IPTC
GET/POST/PUT/DELETE  /api/v1/information-sources[/{id}]              CRUD medios
GET/POST/PUT/DELETE  /api/v1/information-sources/{id}/rss-channels   CRUD canales (anidado)
GET/POST/PUT/DELETE  /api/v1/users/{uid}/alerts[/{aid}]              CRUD alertas (per-usuario)
GET/POST/PUT/DELETE  /api/v1/users/{uid}/alerts/{aid}/notifications  CRUD notificaciones (anidado)
GET/POST/PUT/DELETE  /api/v1/stats[/{id}]                            CRUD stats
```

Ver Swagger UI en http://localhost:8000/docs cuando el backend esté corriendo.

---

## Tecnologías

| Capa | Tecnología | Versión |
|---|---|---|
| Frontend | React | 19 |
| | Vite | 5 |
| | react-i18next | 15 |
| | Recharts | 3.8 |
| | Vitest | 2.1 |
| Backend | FastAPI | 0.115 |
| | SQLAlchemy | 2.0 |
| | Alembic | 1.18 |
| | APScheduler | 3.10 |
| | feedparser | latest |
| | pytest + pytest-cov | 9 / 7 |
| | Ruff | latest |
| BD | PostgreSQL | 18 |
| Email (dev) | MailHog | 1.0 |
| Auth | JWT (PyJWT + bcrypt) | — |
| Orquestación | Docker Compose | — |
| CI | GitHub Actions | — |

---

## Estado del proyecto

Ver [`docs/REPARTO_FINAL.md`](docs/REPARTO_FINAL.md) para el estado actualizado.

**Resumen actual:** 38/40 ✅ del [`DOSS-CHECKLIST_2026`](docs/traceability.md). Las 2 partes pendientes (CD pipeline + SonarQube) están asignadas y son la última fase antes de la entrega.

---

## Equipo y workflow

Desarrollo colaborativo en GitHub:

- Una rama por persona y tarea: `feature/<nombre>-<tema>` o `fix/<tema>`
- PR a `main` con review mínima de 1 compañero
- CI debe estar verde antes de mergear
- Cada commit con cuenta de la uni configurada localmente

Historia de contribuciones por sprint en [`ROADMAP.md`](ROADMAP.md) y [`BACKLOG.md`](BACKLOG.md).

---

## Licencia

Proyecto académico — UC3M DevOps 2025/26.
