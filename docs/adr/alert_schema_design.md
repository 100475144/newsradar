# ADR — Diseño del schema de alertas y alineación con la API oficial

## Contexto

NEWSRADAR define un contrato API oficial distribuido por el profesor (T6.4) que establece la estructura canónica de una alerta. Durante el desarrollo del proyecto, el schema ha evolucionado desde una versión inicial hasta el modelo oficial, incorporando además campos internos necesarios para el flujo de matching y notificaciones que no forman parte del contrato público.

La tensión principal que resuelve este ADR es: **cómo cumplir exactamente el contrato API oficial sin perder la funcionalidad interna** que el sistema necesita para operar (matching textual, preferencias de notificación, activación/desactivación de alertas).

El módulo `alerts` necesita que su schema sea coherente con tres realidades simultáneas:

1. El contrato OpenAPI oficial que el evaluador verificará automáticamente.
2. Los campos internos que el motor de matching (`matching.py`) necesita para funcionar.
3. Los campos de configuración que la interfaz de usuario necesita exponer al gestor.


## Decisión

Se adopta un diseño de schema con estas características:

1. El schema oficial (`AlertBase`) replica exactamente el modelo del contrato T6.4 sin añadir ni eliminar campos expuestos.
2. Los campos internos (`keyword`, `notify_in_app`, `notify_email`, `is_active`) se mantienen en el modelo ORM y en schemas extendidos, pero **no se exponen** en los endpoints oficiales.
3. Se definen tres schemas de entrada diferenciados: `AlertCreate` (oficial), `AlertCreateInternal` (UI propia) y `AlertUpdate` (actualización parcial).
4. `AlertResponse` extiende `AlertBase` con `id`, `user_id` y los campos internos, ya que la UI los necesita para renderizar el estado completo de una alerta.
5. Las categorías se almacenan como lista JSONB de objetos `{code, label}` alineada con el tipo `AlertCategoryItem` del contrato oficial.
6. Los identificadores de fuentes (`rss_channels_ids`, `information_sources_ids`) se almacenan como listas JSONB de strings, no de enteros, siguiendo el contrato oficial.
7. La validación de `cron_expression` se aplica en el schema con una regex de 5 campos estándar.


## Justificación

### 1. Separación entre schema oficial y schema interno

El contrato T6.4 define `AlertBase` con los campos:

```
name, descriptors, categories, rss_channels_ids,
information_sources_ids, cron_expression
```

Estos son los campos que el evaluador verificará en los endpoints `GET/POST /users/{user_id}/alerts`. Añadir campos adicionales a la respuesta oficial podría romper tests de validación estricta que no esperen propiedades extra.

Sin embargo, la UI necesita saber si una alerta está activa, qué canales de notificación tiene configurados y cuál es su keyword principal. Por eso `AlertResponse` extiende `AlertBase` añadiendo los campos internos. Esta es la respuesta que devuelven todos los endpoints (incluidos los oficiales), lo que supone una extensión conservadora del contrato: los campos extra no rompen parsers que ignoren propiedades desconocidas, y aportan la información que la UI necesita.

### 2. Evolución desde `created_by`/`expanded_keywords`/`category`/`source_ids`

La versión inicial del modelo usaba:

- `created_by` (FK al usuario creador) → reemplazado por `user_id` para alinearse con el campo `Alert.user_id` del contrato oficial.
- `expanded_keywords: List[str]` → reemplazado por `descriptors: List[str]` (mismo contenido semántico, nombre oficial).
- `category: str` → reemplazado por `categories: List[{code, label}]` para soportar múltiples categorías IPTC por alerta, siguiendo el modelo oficial.
- `source_ids: List[int]` → dividido en `rss_channels_ids: List[str]` e `information_sources_ids: List[str]` para distinguir entre canales RSS concretos y fuentes de información (medios), y para usar strings en lugar de enteros como exige el contrato.

Estos cambios son breaking changes en la BD. Se gestionan mediante migraciones Alembic. Los campos internos que no aparecen en el contrato oficial (`keyword`, `notify_in_app`, `notify_email`, `is_active`) se conservan sin renombrar porque son propios del sistema.

### 3. Categorías como lista JSONB de `{code, label}`

El contrato oficial usa `List[AlertCategoryItem]` con campos `code` y `label`. Se eligió JSONB en lugar de una tabla relacional `alert_categories` por las siguientes razones:

- El número de categorías por alerta es pequeño (las IPTC de primer nivel son ~20).
- La consulta más frecuente es leer todas las categorías de una alerta en un solo acceso, no filtrar alertas por categoría con JOIN.
- JSONB permite indexar el primer elemento con `Alert.categories[0]["code"].astext` para estadísticas de dashboard sin tabla adicional.
- Reduce el número de tablas y la complejidad del schema de BD para una funcionalidad secundaria.

### 4. IDs de fuentes como `List[str]` en lugar de `List[int]`

El contrato oficial declara `rss_channels_ids` e `information_sources_ids` como listas de strings. Aunque los IDs internos son enteros, se almacenan y se envían como strings para cumplir exactamente el contrato. La función `_normalize_id_list` en `service.py` convierte cualquier valor a string y deduplica antes de persistir.

En `matching.py`, la comparación se hace con `str(channel.id)` y `str(channel.information_source_id)`, alineando la representación interna con la del contrato.

### 5. Separación `keyword` / `descriptors`

El campo `keyword` es el término principal que el usuario introduce al crear la alerta. `descriptors` son los términos expandidos (sinónimos, relacionados) que el usuario acepta opcionalmente.

Se mantienen separados porque tienen ciclos de vida distintos:

- `keyword` es inmutable desde la creación (identifica semánticamente la alerta).
- `descriptors` puede actualizarse independientemente (el usuario puede añadir o quitar sinónimos sin cambiar la alerta).

El motor de matching (`_alert_terms`) los combina en tiempo de ejecución, tratándolos como un pool único de términos de búsqueda. Esta separación también facilita que el endpoint de sugerencias (`GET /alerts/suggestions/{keyword}`) opere sobre la keyword sin necesitar la alerta completa.

### 6. Validación de `cron_expression` en el schema

La expresión cron se valida con una regex de 5 campos estándar directamente en `AlertBase` mediante `@field_validator`. Esto garantiza que ninguna alerta con cron inválido llega a la base de datos, devolviendo un `422 Unprocessable Entity` con mensaje descriptivo.

Se valida en el schema (no en el servicio) porque es una restricción de formato, no de negocio: aplica en todos los contextos de entrada (`AlertCreate`, `AlertCreateInternal`, `AlertUpdate`) y no depende de estado externo.

### 7. Límite de 20 alertas por usuario

El enunciado establece un máximo de 20 alertas por gestor. Se implementa en `AlertService.create_alert` (capa de servicio) con una consulta `count_for_user` antes de la inserción, devolviendo `400 Bad Request` si se supera el límite. Se sitúa en el servicio (no en el schema ni en la BD) porque es una regla de negocio que depende de estado externo (el número actual de alertas del usuario).


## Diseño resultante

### Jerarquía de schemas

```
AlertCategoryItem          {code: str, label: str}

AlertBase                  name, descriptors, categories, rss_channels_ids,
    (oficial T6.4)         information_sources_ids, cron_expression
        │
        ├── AlertCreate          POST oficial (sin campos extra)
        │
        └── AlertCreateInternal  POST UI propia (+ keyword, notify_in_app, notify_email)

AlertUpdate                Todos los campos opcionales (PATCH semántico vía PUT)

AlertResponse              AlertBase + id + user_id
    (respuesta unificada)  + keyword + notify_in_app + notify_email + is_active
```

### Campos del modelo ORM `Alert`

```
# Campos oficiales
name                  str(200)
descriptors           JSONB  [str, ...]
categories            JSONB  [{code, label}, ...]
rss_channels_ids      JSONB  [str, ...]
information_sources_ids JSONB [str, ...]
cron_expression       str(120)
user_id               FK users.id

# Campos internos
keyword               str(200)  nullable
is_active             bool      default True
notify_in_app         bool      default True
notify_email          bool      default False
```

### Normalización aplicada al guardar

| Campo | Normalización |
|-------|--------------|
| `name` | `.strip()` |
| `descriptors` | strip + lowercase dedup + eliminar vacíos |
| `categories` | lowercase code dedup + label desde IPTC si falta |
| `rss_channels_ids` | `str()` + strip + dedup |
| `information_sources_ids` | `str()` + strip + dedup |
| `cron_expression` | `.strip()` + regex 5 campos |

### Endpoints que usan cada schema

```
POST   /users/{user_id}/alerts          → AlertCreateInternal (payload)  → AlertResponse
GET    /users/{user_id}/alerts          →                                   AlertResponse[]
GET    /users/{user_id}/alerts/{id}     →                                   AlertResponse
PUT    /users/{user_id}/alerts/{id}     → AlertUpdate (payload)           → AlertResponse
DELETE /users/{user_id}/alerts/{id}     →                                   204
PATCH  /users/{user_id}/alerts/{id}/activate   →                          AlertResponse
PATCH  /users/{user_id}/alerts/{id}/deactivate →                          AlertResponse
```


## Consecuencias

- El uso de `AlertCreateInternal` en el endpoint `POST` oficial (en lugar de `AlertCreate`) expone campos no oficiales en el request body. Esto es una extensión aditiva: el evaluador puede enviar un payload sin esos campos y funcionará correctamente porque todos son opcionales.
- El almacenamiento JSONB de `categories` y `rss_channels_ids` es eficiente para lectura pero requiere operadores específicos de Postgres para queries analíticas (como la agrupación por categoría en el dashboard). Esto se acepta porque las queries de dashboard son poco frecuentes y el sistema ya tiene Postgres como BD principal.
- Cualquier cambio futuro en el contrato T6.4 que añada campos a `AlertBase` requiere: (1) actualizar el schema Pydantic, (2) añadir la columna en el modelo ORM, (3) generar una migración Alembic. La separación de responsabilidades entre schemas hace que estos cambios sean localizados y predecibles.
