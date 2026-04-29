# Diagrama de despliegue (arquitectura física)

Servicios definidos en `docker-compose.yaml`. Cada bloque es un contenedor
Docker; las flechas indican comunicación de red entre ellos.

```mermaid
flowchart LR
    Dev[(Desarrollador<br/>localhost)]

    subgraph Compose["docker-compose"]
        UI["ui<br/>node:20<br/>vite :5173"]
        API["api<br/>python:3.13<br/>uvicorn :8000"]
        DB[("db<br/>postgres:18<br/>:5432")]
        Mail["mailhog<br/>:1025 SMTP<br/>:8025 UI"]
    end

    Dev -- "http://localhost:5173" --> UI
    Dev -- "http://localhost:8000/api/v1/health" --> API
    Dev -- "http://localhost:8025 (MailHog UI)" --> Mail
    UI -- "/api/v1/* (CORS)" --> API
    API -- "psycopg+v3 5432" --> DB
    API -- "smtp 1025" --> Mail
    API -- "feedparser HTTPS" --> Internet[(Internet)]

    classDef external fill:#fff,stroke:#888,color:#666;
    classDef storage fill:#eef,stroke:#446,color:#113;
    class Internet,Dev external;
    class DB storage;
```

## Salud y arranque

- `api` espera al healthcheck de `db` (`pg_isready`).
- En el `lifespan` arranca:
  1. `_seed_admin_user()` → crea el admin si no existe (checklist #21).
  2. `_seed_rss_sources()` → siembra ~110 canales (checklist #13-15).
  3. `CrawlerScheduler.start()` con la cron expression configurada.
- El healthcheck de `api` apunta a `GET /api/v1/health` (checklist #28).

## Volúmenes

- `postgres_data` — persistencia de la BD entre reinicios. Se borra con
  `docker compose down -v` (necesario tras cambios destructivos en migraciones).
- `frontend_node_modules` — cache de `node_modules` para acelerar cold start.
