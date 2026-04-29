# Arquitectura del sistema

> Documento técnico generado en Fase 2 (D3). Acompaña a los diagramas de
> [bloques](diagrams/architecture.md), [secuencia](diagrams/sequence-notification.md)
> y [despliegue](diagrams/deployment.md).

## 1. Visión global

NEWSRADAR es un sistema de **monitorización de noticias** organizado en tres
capas físicas y siete módulos lógicos:

| Capa | Tecnología | Responsabilidad |
|---|---|---|
| Frontend | React 19 + Vite + react-i18next + Recharts | UI/UX, autenticación cliente, dashboard, gestión de alertas/sources |
| Backend (API) | FastAPI + SQLAlchemy 2 + Alembic + APScheduler | Lógica de negocio, REST, crawling, matching, notificaciones |
| Persistencia | PostgreSQL 18 (psycopg v3) | Almacén relacional + JSONB para campos flexibles |
| Infra dev | Docker Compose + MailHog | Aislamiento, reproducibilidad, captura de emails |

## 2. Módulos del backend

| Módulo | Carpeta | Tablas principales | Endpoints (resumen) |
|---|---|---|---|
| `auth` | `app/modules/auth` | `users`, `roles`, `user_roles`, `email_verification_tokens` | `/auth/*`, `/users/*` (CRUD), `/roles/*` (CRUD) |
| `sources` | `app/modules/sources` | `categories`, `information_sources`, `rss_channels` | `/categories/*`, `/information-sources/*`, anidados `/rss-channels/*` |
| `news` | `app/modules/news` | `news` | `/news/*`, `/news/me/*` |
| `alerts` | `app/modules/alerts` | `alerts` | `/users/{id}/alerts/*`, atajos `/users/me/alerts`, `/alerts/categories`, `/alerts/suggestions/{kw}` |
| `notifications` | `app/modules/notifications` | `notifications` | `/users/{id}/alerts/{aid}/notifications/*` (oficial), `/users/me/notifications/*` (UI) |
| `crawler` | `app/modules/crawler` | — (consume sources, escribe news) | Trabajo background (APScheduler) |
| `stats` | `app/modules/stats` | `stats` | `/stats/*` (oficial) |

Cada módulo sigue el patrón **API → Service → Repository**:

- **API** (`*_api.py` o `api.py`): routers FastAPI; valida con schemas Pydantic.
- **Service**: lógica de negocio pura; lanza excepciones HTTP.
- **Repository**: queries SQLAlchemy; nunca depende de FastAPI.
- **Models**: ORM (`SQLAlchemy 2.0`).
- **Schemas**: Pydantic v2 con `ConfigDict(from_attributes=True)`.

Esta segmentación es la que se cita en la **guía de extensión** para añadir
una funcionalidad nueva sin tocar los módulos existentes.

## 3. Flujos clave

### 3.1 Registro y verificación de email

1. `POST /auth/register` con `{email, password, first_name, last_name, organization}`.
2. `AuthService.register_user`:
   - hash bcrypt + INSERT en `users`.
   - asigna `gestor` automáticamente vía `role_ids` (CAMBIO #1bis).
   - genera token aleatorio (24h) y lo guarda en `email_verification_tokens`.
   - manda email vía SMTP (MailHog en dev) con un enlace `/verify-email?token=…`.
3. El usuario hace click → `GET /auth/verify-email?token=…` → marca `is_verified=True`.

### 3.2 Crawling y matching (atómico, duda 21-abr)

Ver [diagrama de secuencia](diagrams/sequence-notification.md). En resumen:

1. APScheduler dispara `CrawlerScheduler._run_cycle()` según cron.
2. El servicio carga todos los `RSSChannel` activos.
3. Por cada feed, parsea con `feedparser`, deduplica (link / external_id /
   content_hash) y crea filas en `news`.
4. Tras cada `News` creada llama a `process_alerts_for_news()` que:
   - filtra alertas activas.
   - aplica filtros por `rss_channels_ids` / `information_sources_ids` o
     por categoría del canal si no hay filtros.
   - genera notificaciones in-app y, si la alerta pide email, envía vía SMTP.

### 3.3 Dashboard per-user (CAMBIO #2)

`/news/me/stats`, `/news/me/wordcloud` y `/alerts/me/stats` calculan
**solo con las noticias** que han generado al menos una notificación para
el usuario logueado:

```sql
SELECT n.* FROM news n WHERE n.id IN (
    SELECT DISTINCT notif.news_id
    FROM notifications notif WHERE notif.user_id = :me
)
```

Esto cumple literalmente la duda del 28-abr ("la información se genera
solamente con los datos del usuario que está logueado").

## 4. Decisiones de diseño

Cada decisión de arquitectura está registrada como ADR en
[`docs/adr/`](adr/). Las más importantes:

- **Roles como entidad** (T6.2): para alinearnos con la API oficial donde
  `User.role_ids: List[int]` apunta a una tabla `roles`.
- **Sources split** (T6.3): la API oficial separa `InformationSource`
  (medio) de `RSSChannel` (feed concreto). Mantenemos los IDs durante el
  backfill para no invalidar `news.source_id`.
- **Matching per-usuario** (T6.4 + CAMBIO #2): cada alerta es propiedad de
  un único gestor; las notificaciones nunca se duplican entre usuarios.
- **Notifications con timestamp + metrics** (T6.5): el modelo oficial es
  abstracto; mantenemos campos internos (`title`, `message`, `is_read`)
  expuestos por `/users/me/notifications/{id}/details` (endpoint añadido).
- **`uq_notification_user_alert_news`**: evita generar varias
  notificaciones para el mismo trío `(user, alert, news)`.

## 5. Cumplimiento del checklist (resumen)

Tras Fase 1 + Fase 2 cubrimos:

- 30/40 ✅ checks de proyecto en green.
- 7/40 🟡 parciales (dashboard per-user pendiente solo de cerrar UI).
- 3/40 ❌ pendientes (CD pipeline, Sonar, traceability/prompts) → Fase 3.

Detalle vivo en [`REPARTO_FINAL.md`](REPARTO_FINAL.md).
