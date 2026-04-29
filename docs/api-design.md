# Diseño de API

Toda la API se sirve bajo el prefijo `/api/v1`. La especificación completa
está disponible en `/api/v1/docs` (Swagger UI, generado automáticamente por
FastAPI). Este documento describe el contrato funcional y la traza con la
API oficial entregada por el profesor (`main.py` aula global).

## Convenciones

- **Auth**: JWT en header `Authorization: Bearer <token>`. Login: `POST /auth/login`.
- **Errores**: respuesta `{ "detail": "..." }` en 4xx. Validaciones Pydantic
  devuelven 422 con la lista de errores.
- **Paginación**: `?skip=0&limit=20` en endpoints que lo soportan.
- **JSONB**: campos como `categories`, `descriptors`, `metrics` viajan como
  arrays de objetos JSON.

## Endpoints oficiales (idénticos al `main.py` del aula global)

### Health

```
GET    /api/v1/health            → { status: "ok", timestamp }
```

### Auth

```
POST   /api/v1/auth/login        → TokenResponse{ access_token, token_type, user }
POST   /api/v1/auth/register     → UserResponse (status 201)
```

### Users

```
GET    /api/v1/users                   → User[]
POST   /api/v1/users                   → User (admin only, 201)
GET    /api/v1/users/{user_id}         → User
PUT    /api/v1/users/{user_id}         → User
DELETE /api/v1/users/{user_id}         → 204
```

`User` = `{ id, email, first_name, last_name, organization, role_ids[] }`
+ campos internos `role`, `is_active`, `is_verified`, `created_at`,
`updated_at` (no en la API oficial pero tolerados como adición).

### Roles

```
GET    /api/v1/roles                   → Role[]
POST   /api/v1/roles                   → Role (201)
GET    /api/v1/roles/{role_id}         → Role
PUT    /api/v1/roles/{role_id}         → Role
DELETE /api/v1/roles/{role_id}         → 204
```

`Role` = `{ id, name }`. Seed inicial: `admin` (id 1) + `gestor` (id 2).

### Categories

```
GET    /api/v1/categories                  → Category[]
POST   /api/v1/categories                  → Category (201)
GET    /api/v1/categories/{category_id}    → Category
PUT    /api/v1/categories/{category_id}    → Category
DELETE /api/v1/categories/{category_id}    → 204
```

`Category` = `{ id, name, source = "IPTC" }`. Seed: las 17 categorías de
primer nivel IPTC + `uncategorized` como fallback.

### Information Sources + RSS Channels (anidado)

```
GET    /api/v1/information-sources                            → InformationSource[]
POST   /api/v1/information-sources                            → InformationSource (201)
GET    /api/v1/information-sources/{source_id}                → InformationSource
PUT    /api/v1/information-sources/{source_id}                → InformationSource
DELETE /api/v1/information-sources/{source_id}                → 204

GET    /api/v1/information-sources/{source_id}/rss-channels                       → RSSChannel[]
POST   /api/v1/information-sources/{source_id}/rss-channels                       → RSSChannel (201)
GET    /api/v1/information-sources/{source_id}/rss-channels/{channel_id}          → RSSChannel
PUT    /api/v1/information-sources/{source_id}/rss-channels/{channel_id}          → RSSChannel
DELETE /api/v1/information-sources/{source_id}/rss-channels/{channel_id}          → 204
```

### Alerts (anidado bajo `/users/{user_id}`)

```
GET    /api/v1/users/{user_id}/alerts                               → Alert[]
POST   /api/v1/users/{user_id}/alerts                               → Alert (201)
GET    /api/v1/users/{user_id}/alerts/{alert_id}                    → Alert
PUT    /api/v1/users/{user_id}/alerts/{alert_id}                    → Alert
DELETE /api/v1/users/{user_id}/alerts/{alert_id}                    → 204
```

`Alert` (oficial) = `{ id, user_id, name, descriptors[], categories[{code,label}],
rss_channels_ids[], information_sources_ids[], cron_expression }` + campos
internos (`keyword`, `notify_in_app`, `notify_email`, `is_active`).

### Notifications (anidado bajo alerts)

```
GET    /api/v1/users/{user_id}/alerts/{alert_id}/notifications                       → Notification[]
POST   /api/v1/users/{user_id}/alerts/{alert_id}/notifications                       → Notification (201)
GET    /api/v1/users/{user_id}/alerts/{alert_id}/notifications/{notification_id}     → Notification
PUT    /api/v1/users/{user_id}/alerts/{alert_id}/notifications/{notification_id}     → Notification
DELETE /api/v1/users/{user_id}/alerts/{alert_id}/notifications/{notification_id}     → 204
```

`Notification` (oficial) = `{ id, alert_id, timestamp, metrics: [{name, value: float}] }`.

### Stats

```
GET    /api/v1/stats                       → Stats[]
POST   /api/v1/stats                       → Stats (201)
GET    /api/v1/stats/{stats_id}            → Stats
PUT    /api/v1/stats/{stats_id}            → Stats
DELETE /api/v1/stats/{stats_id}            → 204
```

`Stats` = `{ id, metrics: [{name, value: float}] }`.

## Endpoints añadidos sobre el contrato oficial (permitidos por el profesor)

### Auth (verificación de email + admin)

```
GET    /api/v1/auth/verify-email?token=…
POST   /api/v1/auth/resend-verification?email=…
POST   /api/v1/auth/login (alias OAuth2 form)
GET    /api/v1/auth/me                     → user actual
GET    /api/v1/auth/users                  → admin only
PATCH  /api/v1/auth/users/{user_id}/role   → admin only
```

### Atajos `/users/me/*` (el frontend evita pasar el user_id explícito)

```
GET    /api/v1/users/me/alerts
POST   /api/v1/users/me/alerts
GET    /api/v1/users/me/notifications
GET    /api/v1/users/me/notifications/{id}/details
PATCH  /api/v1/users/me/notifications/{id}/read
PATCH  /api/v1/users/me/notifications/{id}/unread
DELETE /api/v1/users/me/notifications/{id}
```

### Activación / desactivación

```
PATCH  /api/v1/users/{u}/alerts/{a}/activate
PATCH  /api/v1/users/{u}/alerts/{a}/deactivate
PATCH  /api/v1/information-sources/{s}/rss-channels/{c}/activate
PATCH  /api/v1/information-sources/{s}/rss-channels/{c}/deactivate
```

### Helpers de alertas

```
GET    /api/v1/alerts/categories                → 17 categorías IPTC con label
GET    /api/v1/alerts/suggestions/{keyword}     → 3-10 descriptors (recommender)
GET    /api/v1/alerts/me/stats                  → alertas/categoría del user logueado
```

### News (no existe en la API oficial, añadido bajo este nombre)

```
GET    /api/v1/news?skip=&limit=&source_id=&category=
GET    /api/v1/news/{news_id}
GET    /api/v1/news/stats              → globales
GET    /api/v1/news/wordcloud          → globales
GET    /api/v1/news/me/stats           → solo noticias matcheadas con alertas del user
GET    /api/v1/news/me/wordcloud       → idem
```

### Crawler (manual trigger / observabilidad)

```
GET    /api/v1/crawler/...             → estado / disparo manual (uso interno)
```

### Catálogo summary y health DB

```
GET    /api/v1/information-sources/catalog/summary    → { total_channels, total_media_outlets, iptc_categories_covered, ... }
GET    /api/v1/health/db                              → ping a Postgres
```

## Trazabilidad con la API oficial

El `main.py` oficial define exactamente los siguientes objetos:

| Modelo oficial | Implementación nuestra | Notas |
|---|---|---|
| `Metric{name, value: float}` | `notifications.schemas.Metric` | Reutilizado en notifications + stats. |
| `Role{id, name}` | `auth.models.Role` | Tabla con seed admin/gestor. |
| `User{id, email, first_name, last_name, organization, role_ids}` | `auth.models.User` + `UserResponse` | + campos internos no expuestos en API canónica. |
| `AlertCategoryItem{code, label}` | `alerts.schemas.AlertCategoryItem` | |
| `AlertBase{name, descriptors, categories, rss_channels_ids, information_sources_ids, cron_expression}` | `alerts.schemas.AlertBase` | + campos internos `keyword`, `notify_*`. |
| `Category{id, name, source="IPTC"}` | `sources.models.Category` | |
| `Notification{id, alert_id, timestamp, metrics}` | `notifications.models.Notification` | + internos para UI; expuestos vía `/users/me/notifications/{id}/details`. |
| `InformationSource{id, name, url}` | `sources.models.InformationSource` | |
| `RSSChannel{id, url, category_id, information_source_id}` | `sources.models.RSSChannel` | + `name`, `is_active` internos. |
| `Stats{id, metrics}` | `stats.models.Stats` | |

Todas las operaciones del oficial están implementadas (todas las `POST`,
`GET`, `PUT`, `DELETE` listadas en `main.py`). Las que añadimos están
explícitamente etiquetadas como añadidas en este documento.
