# Diagrama de secuencia — RSS → notificación

Flujo completo desde el tick del scheduler hasta que el usuario ve la
notificación en la bandeja de entrada y/o recibe el email.

```mermaid
sequenceDiagram
    autonumber
    participant Cron as APScheduler<br/>(cron tick)
    participant Crawler as crawler.service
    participant Feed as Feed RSS<br/>(externo)
    participant DB as PostgreSQL
    participant Match as alerts.matching
    participant NotifRepo as notifications.repository
    participant Mail as MailHog<br/>(SMTP)
    participant UI as Frontend<br/>(NotificationsPage)

    Cron->>Crawler: run_cycle()
    Crawler->>DB: SELECT rss_channels WHERE is_active
    loop por cada canal activo
        Crawler->>Feed: GET feed.xml
        Feed-->>Crawler: items RSS
        loop por cada entry
            Crawler->>DB: deduplicate (link / external_id / hash)
            Crawler->>DB: INSERT INTO news
            Crawler->>Match: process_alerts_for_news(news)
            Match->>DB: SELECT alerts WHERE is_active
            Match->>Match: filtrar por descriptors / categories / channels
            alt match
                Match->>NotifRepo: create(title, message, metrics, ts)
                NotifRepo->>DB: INSERT INTO notifications
                opt notify_email = true
                    Match->>Mail: send_email_notification(to, subject, body)
                end
            end
        end
    end

    Note over UI,DB: Más tarde, el usuario abre la app
    UI->>DB: GET /api/v1/users/me/notifications
    DB-->>UI: lista (NotificationDetailResponse)
    UI->>DB: PATCH /notifications/{id}/read
```

## Reglas clave

- **Atomicidad** (duda 21-abr): captura → análisis → guardado en un solo
  proceso. Si una entry falla, las anteriores ya fueron commiteadas y el
  ciclo continúa con la siguiente.
- **Per-usuario** (CAMBIO #2): cada notificación se asocia al `owner` de la
  alerta. Otros usuarios no la ven aunque la news sea la misma.
- **Deduplicación**: la unique constraint `uq_notification_user_alert_news`
  evita duplicar emails/inbox cuando una news pasa varias veces el matching.
