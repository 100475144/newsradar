# ADR — Diseño del sistema de notificaciones

## Contexto

NEWSRADAR debe notificar a los usuarios cuando el motor de matching detecta que una noticia contiene alguno de los descriptores definidos en sus alertas. El enunciado del proyecto establece que se enviará un mensaje al buzón de la aplicación y, opcionalmente, al correo electrónico del usuario, con el título `"Actualización de <alerta> en <día/hora>"` y un cuerpo con la fuente, fecha, título de la noticia y resumen del RSS.

La adenda del proyecto (cambio oficial ID 1, 22 de abril de 2026) elimina el rol lector, dejando solo usuarios gestores. Esto tiene una consecuencia directa en las notificaciones: **las alertas y sus notificaciones son estrictamente per-usuario**. El panel de mando, el buzón y las estadísticas solo muestran datos del usuario propietario de cada alerta.

El módulo `notifications` debe encajar en la arquitectura modular del proyecto con sus propios `models`, `schemas`, `repository`, `service` y `api`, sin acoplar directamente el motor de matching al módulo de notificaciones.


## Decisión

Se adopta un diseño de notificaciones con estas características:

1. Una notificación se genera exclusivamente desde el motor de matching (`matching.py`), nunca desde la API directamente.
2. La deduplicación se garantiza mediante una clave de entrega compuesta por `(user_id, alert_id, news_id)`, tanto a nivel de restricción única en base de datos como en la capa de repositorio.
3. Se mantienen dos canales de entrega configurables por alerta: buzón in-app (`notify_in_app`) y correo electrónico (`notify_email`).
4. El envío de email se realiza mediante SMTP estándar, sin dependencias de servicios externos de terceros.
5. Las notificaciones son per-usuario: cada propietario de alerta solo recibe y visualiza las suyas propias.
6. El schema oficial (`NotificationResponse`) se expone bajo la ruta anidada canónica; la UI consume un schema enriquecido adicional (`NotificationDetailResponse`) con campos internos no presentes en el contrato oficial.
7. El endpoint `POST` canónico se expone por cumplimiento de contrato pero rechaza la creación manual, ya que las notificaciones son generadas automáticamente.


## Justificación

### 1. Generación exclusiva desde el motor de matching

Las notificaciones son un efecto secundario del matching, no una entidad que el usuario cree directamente. Generarlas únicamente desde `matching.py` (invocado a su vez desde `news/service.py` tras persistir cada noticia) garantiza que toda notificación tiene una noticia y una alerta asociadas, que son las dos condiciones de negocio necesarias para que la notificación tenga sentido.

El endpoint `POST` canónico se mantiene para cumplir el contrato OpenAPI del enunciado, pero devuelve `400` con una explicación clara si se llama directamente.

### 2. Deduplicación por clave `(user_id, alert_id, news_id)`

El motor de matching se ejecuta cada vez que el crawler ingesta una noticia. Si el mismo feed se reprocesa, o si el scheduler dispara varias ejecuciones en poco tiempo, sin deduplicación el mismo usuario podría recibir la misma notificación múltiples veces.

Se aplica la deduplicación en dos niveles complementarios:

- **Base de datos**: restricción `UNIQUE (user_id, alert_id, news_id)` en la tabla `notifications`. Esto garantiza la integridad incluso ante condiciones de carrera.
- **Repositorio**: `get_by_delivery_key` antes de insertar. Si ya existe, se devuelve la notificación existente sin error. Esto evita excepciones de integridad en el flujo normal y permite al llamador tratar el resultado uniformemente.

### 3. Doble canal: in-app y email

La alerta expone dos flags independientes (`notify_in_app`, `notify_email`) que el usuario gestiona por separado. Esto permite configuraciones asimétricas: un usuario puede querer solo buzón in-app para alertas de baja prioridad y solo email para alertas críticas.

El canal in-app crea un registro en la tabla `notifications`. El canal email invoca `send_email_notification` de `email_utils.py`. Ambos canales se evalúan en el mismo ciclo de matching, de forma que si uno falla el otro no se ve afectado.

### 4. SMTP estándar sin servicios de terceros

El envío de email se implementa con `smtplib` de la librería estándar de Python, configurable mediante variables de entorno (`smtp_host`, `smtp_port`, `smtp_username`, `smtp_password`, `smtp_sender`, `smtp_use_tls`). Si `smtp_host` no está configurado, el sistema registra un aviso en el log y continúa sin error.

Esta decisión evita dependencias de terceros (SendGrid, Mailgun, SES) en una fase temprana del proyecto, mantiene el despliegue simple y permite usar cualquier servidor SMTP compatible.

### 5. Notificaciones per-usuario (cambio oficial ID 1)

Tras la eliminación del rol lector, cada usuario gestor opera de forma independiente. Por tanto:

- El modelo `Notification` incluye `user_id` como FK al propietario.
- `NotificationRepository.list_for_user` filtra estrictamente por `user_id`.
- Los endpoints `GET /users/me/notifications` solo devuelven notificaciones del usuario autenticado.
- Las estadísticas de noticias (`/news/me/stats`) y las nubes de palabras (`/news/me/wordcloud`) se calculan a partir de las noticias que tienen al menos una notificación para el usuario, conectando ambos módulos a través de la tabla de notificaciones sin acoplarlos directamente.

### 6. Separación entre schema oficial e interno

El schema oficial del enunciado (`NotificationResponse`) expone únicamente `id`, `alert_id`, `timestamp` y `metrics`. Sin embargo, la UI necesita `title`, `message`, `is_read`, `user_id` y `news_id` para renderizar el buzón de notificaciones.

Se resuelve con dos schemas independientes:

- `NotificationResponse`: contrato oficial, usado en los endpoints anidados `/users/{u}/alerts/{a}/notifications`.
- `NotificationDetailResponse`: schema enriquecido, usado en los endpoints `me` (`/users/me/notifications`).

Esto permite cumplir el contrato del enunciado sin exponer campos internos en los endpoints oficiales, y al mismo tiempo dar al frontend toda la información que necesita a través de los endpoints propios.

### 7. Métricas adjuntas a cada notificación

El enunciado exige que las notificaciones incluyan estadísticas de procesamiento. Se implementa como lista JSONB de objetos `{name: str, value: float}` (`metrics`), generada por `build_default_metrics` en `notifications/service.py`. Las métricas iniciales son:

- `summary_length_chars`: longitud del resumen de la noticia.
- `title_length_chars`: longitud del título.
- `has_known_source`: `1.0` si la noticia proviene de un canal con fuente identificada, `0.0` si no.

Este diseño es extensible: añadir nuevas métricas no requiere cambios de schema en base de datos.


## Diseño resultante

### Flujo de generación de una notificación

```text
crawler ingesta noticia
    -> NewsService.create_news_from_crawler
    -> news persistida en BD
    -> process_alerts_for_news(db, news)          [matching.py]
    -> carga alertas activas
    -> para cada alerta: _news_matches_alert?
        -> NO: descarta
        -> SÍ: _resolve_news_classification       [actualiza categoría de la noticia]
             -> get_by_delivery_key               [¿ya existe esta notificación?]
                -> SÍ: omite (deduplicación)
                -> NO: NotificationRepository.create
                     -> registro en tabla notifications  [si notify_in_app]
                     -> send_email_notification          [si notify_email]
```

### Flujo de backfill al crear/activar una alerta

```text
AlertService.create_alert / activate_alert
    -> _backfill_matching_for_alert(db, alert)
    -> consulta últimas 500 noticias (por published_at DESC)
    -> para cada noticia: mismo flujo de matching y deduplicación
    -> genera notificaciones para noticias pre-existentes que matcheen
```

### Modelo de datos

```
notifications
├── id                PK
├── user_id           FK users.id   (destinatario, per-user)
├── alert_id          FK alerts.id
├── news_id           FK news.id
├── timestamp         datetime (tz)
├── metrics           JSONB  [{name, value}]
├── title             str    (interno, UI)
├── message           str    (interno, UI)
├── is_read           bool   (interno, UI)
└── UNIQUE (user_id, alert_id, news_id)
```

### Estructura de ficheros implicados

```
app/modules/notifications/
├── models.py        # Notification: modelo ORM + UniqueConstraint delivery key
├── schemas.py       # NotificationResponse (oficial) + NotificationDetailResponse (UI)
├── repository.py    # CRUD + get_by_delivery_key + list_for_user/alert
├── service.py       # NotificationService + build_default_metrics
├── email_utils.py   # send_email / send_email_notification / send_verification_email
└── api.py           # Endpoints canónicos + endpoints /me

app/modules/alerts/matching.py   # Invoca NotificationRepository directamente
app/modules/news/service.py      # Invoca process_alerts_for_news tras persistir
```

### Contrato de endpoints

```
# Canónicos (schema oficial)
GET    /api/v1/users/{user_id}/alerts/{alert_id}/notifications
POST   /api/v1/users/{user_id}/alerts/{alert_id}/notifications  → 400 (solo contrato)
GET    /api/v1/users/{user_id}/alerts/{alert_id}/notifications/{id}
PUT    /api/v1/users/{user_id}/alerts/{alert_id}/notifications/{id}
DELETE /api/v1/users/{user_id}/alerts/{alert_id}/notifications/{id}

# Añadidos para la UI (schema enriquecido)
GET    /api/v1/users/me/notifications
GET    /api/v1/users/me/notifications/{id}/details
PATCH  /api/v1/users/me/notifications/{id}/read
PATCH  /api/v1/users/me/notifications/{id}/unread
DELETE /api/v1/users/me/notifications/{id}
```

### Formato del título y cuerpo (enunciado)

```
Título:  "Actualización de <nombre_alerta> en <dd/mm/yyyy HH:MM>"
Cuerpo:
    Fuente: <nombre_medio o "Desconocida">
    Fecha:  <fecha_publicacion>
    Título: <titulo_noticia>

    <resumen_rss o "Sin resumen disponible.">

    Enlace: <url>   (solo en email)
```


## Consecuencias

- La deduplicación a dos niveles (BD + repositorio) hace el sistema robusto frente a reinicios del crawler y condiciones de carrera sin coste de complejidad significativo.
- El acoplamiento entre `matching.py` y `NotificationRepository` es directo e intencional: el motor de matching es el único punto de creación de notificaciones, lo que facilita el razonamiento sobre cuándo y por qué se genera cada notificación.
- Si en el futuro se quiere añadir un canal adicional (push, Slack, webhook), el punto de extensión es `matching.py` junto a un nuevo flag en `Alert`, sin necesidad de modificar el repositorio ni el schema.
- El diseño SMTP sin cola de mensajes implica que un fallo de red durante el envío de email no reintentará el envío. En una fase futura se podría introducir una cola (Celery, ARQ) si la fiabilidad del canal email es crítica.
