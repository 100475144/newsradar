# Diagrama de bloques de arquitectura

Capas y módulos del sistema NEWSRADAR. GitHub renderiza el código Mermaid
automáticamente; para regenerarlo a PNG basta con `mmdc -i architecture.md`.

```mermaid
flowchart TB
    subgraph FE["Frontend (React 19 + Vite + i18n)"]
        UI_Login[LoginPage]
        UI_Register[RegisterPage]
        UI_Dashboard[DashboardPage]
        UI_News[NewsPage]
        UI_Sources[SourcesPage]
        UI_Alerts[AlertsPage]
        UI_Notif[NotificationsPage]
    end

    subgraph BE["Backend (FastAPI / api/v1)"]
        direction TB
        subgraph Auth["auth"]
            AuthAPI["api / users_api / roles_api"]
            AuthService[service]
            AuthRepo[repository]
        end
        subgraph Sources["sources"]
            SrcAPI["categories + information-sources + rss-channels"]
            SrcModels[models]
        end
        subgraph Alerts["alerts"]
            AlertsAPI["/users/:id/alerts"]
            AlertsSvc[service]
            AlertsMatch[matching]
            AlertsRecom[recommender]
        end
        subgraph Notifs["notifications"]
            NotifAPI["nested + /users/me"]
            NotifSvc[service]
            NotifEmail[email_utils]
        end
        subgraph Crawler["crawler"]
            CrawlerSvc[service feedparser]
            Sched[APScheduler cron]
        end
        subgraph News["news"]
            NewsAPI["/news + /news/me"]
            NewsSvc[service]
        end
        subgraph Stats["stats"]
            StatsAPI["/stats CRUD"]
        end
    end

    DB[("PostgreSQL 18")]
    Mail[("MailHog SMTP")]
    Feeds[("Feeds RSS externos")]

    FE -->|HTTP /api/v1| BE

    AuthService --> AuthRepo --> DB
    SrcAPI --> SrcModels --> DB
    AlertsAPI --> AlertsSvc --> DB
    AlertsMatch --> NotifSvc
    NotifSvc --> DB
    NotifEmail --> Mail
    CrawlerSvc --> SrcModels
    CrawlerSvc --> NewsSvc --> DB
    NewsSvc --> AlertsMatch
    Sched -. cron tick .-> CrawlerSvc
    CrawlerSvc -->|HTTP GET| Feeds
    NewsAPI --> NewsSvc
    StatsAPI --> DB
```

## Lectura rápida

- **Frontend** habla solo con el backend bajo `/api/v1`.
- **Auth** mantiene `users`, `roles` y email verification tokens.
- **Sources** se ha desdoblado en `Category`, `InformationSource` y `RSSChannel`
  para alinear con la API oficial.
- **Crawler** + **APScheduler** ejecutan un ciclo cron (`*/5 * * * *` por defecto)
  que parsea feeds, crea `News` y dispara el motor de matching.
- **Matching** filtra por descriptors/categories/canales/medios de cada alerta y
  produce notificaciones in-app + emails para el propietario de la alerta
  (CAMBIO #2 oficial: dashboards y notificaciones son per-usuario).
- **Notifications** expone los endpoints anidados oficiales más atajos
  `/users/me/notifications` para la UI.
- **Stats** sigue el contrato oficial (snapshots `{metrics: List[Metric]}`).

> Nota Mermaid: las URL con parámetros se escriben con `:id` en lugar de `{id}`
> porque las llaves chocan con la gramática del parser de GitHub. Conceptualmente
> son los mismos paths anidados oficiales (`/users/{id}/alerts`).
