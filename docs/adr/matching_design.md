# ADR — Diseño del motor de matching entre alertas y noticias

## Contexto

NEWSRADAR necesita un mecanismo que, cada vez que se ingesta una noticia, determine qué alertas activas son relevantes para ella y genere las notificaciones correspondientes. Este proceso es el núcleo funcional del sistema: sin matching no hay notificaciones, sin notificaciones el sistema no cumple su objetivo principal.

El motor de matching debe resolver varios problemas simultáneamente:

- **Filtrado por fuente**: una alerta puede limitarse a canales RSS o medios concretos, o aplicar a todos los canales de una categoría.
- **Matching textual**: los descriptores de la alerta deben aparecer en el título, resumen o autor de la noticia.
- **Clasificación**: cuando una noticia hace match, su categoría puede actualizarse según la alerta que la detectó.
- **Retroactividad**: una alerta recién creada o activada debe generar notificaciones también para noticias ya existentes en el sistema.

La arquitectura del proyecto exige bajo acoplamiento entre módulos. El motor de matching es un punto de intersección entre `alerts`, `news`, `sources` y `notifications`, por lo que su diseño tiene implicaciones en todos ellos.


## Decisión

Se adopta un motor de matching con estas características:

1. El motor de matching residirá en `app/modules/alerts/matching.py`, como componente propio del módulo `alerts`.
2. El matching evaluará alertas activas contra una noticia concreta, no al revés.
3. El filtrado de fuente tendrá precedencia sobre el filtrado por categoría: si la alerta define `rss_channels_ids` o `information_sources_ids`, se filtra por canal/medio; solo si ambos están vacíos se aplica el filtro por categoría IPTC.
4. El matching textual buscará cualquier término (`keyword` + `descriptors`) en el haystack compuesto por título, resumen y autor de la noticia.
5. La clasificación de la noticia se resolverá por votación entre las alertas que hicieron match, seleccionando la categoría más votada (desempate por menor `alert_id`).
6. El backfill (matching retroactivo) se ejecutará al crear o activar una alerta, contra las últimas 500 noticias ordenadas por fecha de publicación descendente.
7. El motor se invocará sincrónicamente desde `NewsService.create_news_from_crawler`, inmediatamente después de persistir cada noticia.


## Justificación

### 1. Matching como componente del módulo alerts

El matching es lógica de negocio del módulo `alerts`: son las alertas las que definen qué buscar y dónde. Situar `matching.py` en `app/modules/alerts/` hace explícita esta propiedad y evita crear un módulo transversal difícil de ubicar conceptualmente.

El acoplamiento con `notifications` y `news` es necesario e intencional: el matching lee noticias y escribe notificaciones. Este acoplamiento se acepta porque el motor es el único componente del sistema que necesita estas tres dependencias simultáneamente.

### 2. Evaluación alerta por alerta contra una noticia

El flujo natural del sistema es: llega una noticia → ¿qué alertas le aplican? Esta dirección (noticia → alertas) es más eficiente que la alternativa (alerta → noticias) cuando el volumen de noticias nuevas es bajo y el de alertas activas es moderado (máximo 20 por usuario, múltiples usuarios).

Además, este enfoque se integra directamente con el ciclo de vida de la noticia: el matching se dispara justo después de persistir, lo que minimiza la latencia entre la publicación de una noticia y la generación de la notificación.

### 3. Precedencia: filtro de canal/fuente sobre filtro de categoría

El enunciado indica que por omisión se usarán todos los canales que pertenezcan a la misma categoría. Esto implica que el filtro por categoría es el fallback cuando no se han especificado canales o medios concretos.

La implementación refleja esta semántica:

```python
if rss_filter or info_filter:
    # Filtro explícito: la noticia debe venir de uno de los canales/medios indicados.
    ...
else:
    # Sin filtro explícito: comparar la categoría del canal de la noticia
    # con las categorías de la alerta.
    ...
```

Esta lógica es más predecible para el usuario que una combinación OR de ambos filtros.

### 4. Matching textual: any-term sobre haystack compuesto

Los descriptores y la keyword de la alerta se normalizan a minúsculas y se buscan como substrings en un haystack que concatena título, resumen y autor de la noticia. Se usa `any()`: basta con que un solo término aparezca para que haya match.

Esta decisión prioriza la cobertura (recall) sobre la precisión: es preferible generar alguna notificación falsa positiva que perder noticias relevantes. En el contexto de monitorización de medios, una notificación de más es menos dañina que una noticia relevante no detectada.

La función `_alert_terms` deduplica los términos manteniendo orden, combinando `keyword` (campo interno) y `descriptors` (campo oficial). Si no hay ningún término definido, la alerta no hace match con ninguna noticia, lo que evita notificaciones masivas por alertas vacías.

### 5. Clasificación por votación con desempate determinista

Cuando varias alertas hacen match sobre la misma noticia, cada una puede proponer una categoría distinta. Se resuelve con una votación simple:

1. Se cuenta cuántas alertas proponen cada código de categoría.
2. Se selecciona el código con más votos.
3. En caso de empate, se selecciona el código cuya alerta tiene el menor `id` (la más antigua), garantizando determinismo.

Si ninguna alerta aporta categoría, la noticia conserva su categoría original (asignada por el canal RSS) y el campo `classification_origin` queda como `"unknown"`. Si alguna alerta aporta categoría, `classification_origin` se actualiza a `"alert"`, dejando trazabilidad del origen de la clasificación.

### 6. Backfill retroactivo al crear o activar alertas

Sin backfill, una alerta recién creada solo captaría noticias futuras, perdiendo todo el histórico relevante ya existente en el sistema. El enunciado no especifica este comportamiento, pero es esperable desde el punto de vista del usuario.

Se limita el backfill a las últimas 500 noticias (por `published_at DESC`) para evitar que la creación de una alerta bloquee el sistema en bases de datos con gran volumen de noticias. Este límite es configurable mediante el parámetro `lookback` de `_backfill_matching_for_alert`.

El backfill aplica la misma lógica de deduplicación que el matching en tiempo real: si la notificación ya existe para esa tripleta `(user_id, alert_id, news_id)`, se omite.

### 7. Ejecución síncrona desde el servicio de noticias

El matching se invoca sincrónicamente desde `NewsService.create_news_from_crawler`, inmediatamente después de `repository.create`. Esta decisión simplifica el flujo inicial: no se necesita una cola de mensajes, un worker externo ni coordinación adicional.

La contrapartida es que si el matching tarda (muchas alertas activas, backfill grande), la respuesta del crawler se retrasa. En una fase futura se puede mover el matching a una tarea asíncrona (Celery, ARQ, BackgroundTasks de FastAPI) si se detecta que es un cuello de botella.


## Diseño resultante

### Algoritmo de matching

```text
process_alerts_for_news(db, news):
    1. Cargar todas las alertas activas ordenadas por id ASC
    2. Resolver canal RSS y categoría del canal para la noticia
    3. Para cada alerta:
        a. _news_matches_alert(news, alert, channel, channel_category)
            i.  ¿alerta activa? → NO: descarta
            ii. ¿hay filtro rss/info? → comparar channel_id / info_source_id
            iii. ¿sin filtro? → comparar categoría del canal con categorías de la alerta
            iv. ¿haystack contiene algún término? → _alert_terms(alert)
        b. Si match: añadir a matching_alerts
    4. _resolve_news_classification(matching_alerts) → categoría ganadora
    5. Actualizar news.category y news.classification_origin si cambia
    6. Para cada alerta en matching_alerts:
        a. Verificar owner activo y verificado
        b. get_by_delivery_key → si existe: omitir
        c. notify_in_app → NotificationRepository.create
        d. notify_email   → send_email_notification
```

### Estructura de términos de una alerta

```
Alert.keyword      → término primario (campo interno)
Alert.descriptors  → lista de términos aceptados por el usuario (campo oficial)

_alert_terms(alert) = dedup([keyword] + descriptors), en minúsculas
haystack           = lower(title + " " + summary + " " + author)
match              = any(term in haystack for term in terms)
```

### Resolución de clasificación

```
matching_alerts → {category_code: (vote_count, min_alert_id)}
ganadora        = max(votes), desempate por min(alert_id), luego lexicográfico
origin          = "alert" si hay categoría ganadora, "unknown" si no
```

### Estructura de ficheros implicados

```
app/modules/alerts/
├── matching.py          # Motor principal: process_alerts_for_news
│                        # + _news_matches_alert, _alert_terms,
│                        # + _alert_category_codes, _resolve_news_classification
└── service.py           # _backfill_matching_for_alert (retroactividad)

app/modules/news/
└── service.py           # Llama a process_alerts_for_news tras create

app/modules/notifications/
├── repository.py        # get_by_delivery_key + create (deduplicación)
└── email_utils.py       # send_email_notification

app/modules/sources/
└── models.py            # RSSChannel, Category (leídos por el matching)
```


## Consecuencias

- El motor es stateless: no mantiene estado entre ejecuciones. Esto lo hace fácil de testear y de razonar sobre él.
- La ejecución síncrona puede convertirse en un cuello de botella si el número de alertas activas o el volumen de noticias crece significativamente. El punto de extensión para asincronía es `NewsService.create_news_from_crawler`.
- El límite de 500 noticias en el backfill es una heurística. Si el histórico relevante supera ese umbral, puede ajustarse o convertirse en configurable por entorno.
- El matching por substring es sensible a términos cortos o ambiguos (por ejemplo, `"ia"` matchearía en `"gracias"`). En una fase futura se puede refinar con búsqueda de palabras completas o stemming.
