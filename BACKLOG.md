# SPRINT 0 — Preparación de infraestructura

## Objetivo real

Que el proyecto **arranque de verdad** y que cada uno pueda empezar su módulo sin improvisar.

---

## ORDEN EXACTO

## Paso 0.1 — Empieza P6

### Qué toca

Raíz del proyecto y configuración de entorno.

### Archivos que crea o modifica

* `/docker-compose.yml`
* `/.env.example`
* `/backend/Dockerfile`
* `/backend/.env.example`
* `/frontend/Dockerfile`
* `/frontend/.env.example`

### Qué debe hacer

* definir servicios `backend`, `frontend`, `db`
* poner PostgreSQL en compose
* definir variables de entorno base
* dejar puertos definidos

### Resultado esperado

Ya existe la base para levantar contenedores.

---

## Paso 0.2 — Empieza P1 en paralelo con P6

### Qué toca

Esqueleto mínimo del backend.

### Archivos que crea o modifica

* `/backend/app/main.py`
* `/backend/app/api/router.py`
* `/backend/app/api/deps.py`
* `/backend/app/core/config.py`
* `/backend/app/core/security.py`
* `/backend/app/core/logging_config.py`
* `/backend/requirements.txt`

### Qué debe hacer

* crear la app FastAPI
* registrar router principal
* crear endpoint `/health`
* dejar preparada configuración base
* dejar dependencias compartidas vacías pero creadas

### Resultado esperado

El backend puede arrancar aunque aún no tenga lógica real.

---

## Paso 0.3 — Sigue P6

### Qué toca

Conexión real a la base de datos.

### Archivos que crea o modifica

* `/backend/app/core/database.py`
* `/docker-compose.yml`
* `/backend/requirements.txt`

### Qué debe hacer

* conectar FastAPI con PostgreSQL
* definir session/engine/base
* verificar que backend y db se ven dentro de Docker

### Resultado esperado

Backend + DB quedan conectados.

---

## Paso 0.4 — Empieza P5

### Qué toca

Esqueleto mínimo del frontend.

### Archivos que crea o modifica

* `/frontend/package.json`
* `/frontend/src/main.jsx`
* `/frontend/src/App.jsx`
* `/frontend/src/app/router.jsx`
* `/frontend/src/api/client.js`

### Qué debe hacer

* crear React + Vite
* dejar router base
* dejar cliente API apuntando al backend
* probar llamada a `/health`

### Resultado esperado

Frontend arranca y sabe hablar con backend.

---

## Paso 0.5 — Empiezan P2, P3 y P4

Aquí todavía no implementan lógica; solo dejan preparados sus módulos.

---

### P2

#### Archivos que crea

* `/backend/app/modules/sources/api.py`
* `/backend/app/modules/sources/service.py`
* `/backend/app/modules/sources/repository.py`
* `/backend/app/modules/sources/models.py`
* `/backend/app/modules/sources/schemas.py`

#### Qué hace

* crear estructura del módulo `sources`
* dejar schemas/model placeholders

---

### P3

#### Archivos que crea

* `/backend/app/modules/news/api.py`
* `/backend/app/modules/news/service.py`
* `/backend/app/modules/news/repository.py`
* `/backend/app/modules/news/models.py`
* `/backend/app/modules/news/schemas.py`
* `/backend/app/modules/crawler/scheduler.py`
* `/backend/app/modules/crawler/rss_client.py`
* `/backend/app/modules/crawler/parser.py`
* `/backend/app/modules/crawler/service.py`
* `/backend/app/modules/crawler/deduplication.py`

#### Qué hace

* crear estructura `news` y `crawler`

---

### P4

#### Archivos que crea

* `/backend/app/modules/alerts/api.py`
* `/backend/app/modules/alerts/service.py`
* `/backend/app/modules/alerts/repository.py`
* `/backend/app/modules/alerts/models.py`
* `/backend/app/modules/alerts/schemas.py`
* `/backend/app/modules/notifications/api.py`
* `/backend/app/modules/notifications/service.py`
* `/backend/app/modules/notifications/repository.py`
* `/backend/app/modules/notifications/models.py`
* `/backend/app/modules/notifications/schemas.py`

#### Qué hace

* crear estructura `alerts` y `notifications`

---

## Paso 0.6 — Cierra P1

### Qué toca

Router global y coherencia backend.

### Archivos que modifica

* `/backend/app/api/router.py`
* `/backend/app/main.py`

### Qué debe hacer

* dejar preparado el `api router` para que luego se enchufen módulos
* revisar que todos sigan el mismo patrón de carpetas/archivos

### Resultado esperado

Toda la estructura backend queda homogénea.

---

## Paso 0.7 — Cierra P6

### Qué toca

Validación del arranque completo.

### Archivos que modifica

* `/docker-compose.yml`
* `/.env.example`
* `/backend/.env.example`
* `/frontend/.env.example`

### Qué debe hacer

* probar `docker compose up`
* verificar frontend, backend y db
* corregir puertos o variables si falla algo

### Resultado esperado final Sprint 0

Todo el equipo puede clonar y arrancar el proyecto.

---

# SPRINT 1 — Usuarios y autenticación

## Objetivo real

Cerrar auth pronto para que los demás construyan sobre una base real.

---

## ORDEN EXACTO

## Paso 1.1 — Empieza P6

### Qué toca

Migraciones / persistencia base.

### Archivos que crea o modifica

* `/backend/app/core/database.py`
* `/backend/alembic.ini` o configuración de migraciones que uséis
* `/backend/alembic/...` si ya lo tenéis
* `/backend/requirements.txt`

### Qué hace

* dejar sistema de migraciones listo
* preparar entorno para crear tabla `users`

### Resultado esperado

Ya podéis persistir usuarios de verdad.

---

## Paso 1.2 — Empieza P1

### Qué toca

Módulo auth completo.

### Archivos que crea o modifica

* `/backend/app/modules/auth/api.py`
* `/backend/app/modules/auth/service.py`
* `/backend/app/modules/auth/repository.py`
* `/backend/app/modules/auth/models.py`
* `/backend/app/modules/auth/schemas.py`
* `/backend/app/core/security.py`
* `/backend/app/api/deps.py`
* `/backend/app/api/router.py`

### Qué hace

* modelo `User`
* register
* login
* JWT
* `/me`
* dependencia `get_current_user`

### Resultado esperado

Auth backend funcional.

---

## Paso 1.3 — Sigue P6

### Qué toca

Tabla de usuarios y soporte DB.

### Archivos que modifica

* migración de usuarios
* `/backend/app/core/database.py` si hace falta

### Qué hace

* crear tabla `users`
* validar que auth persiste datos bien

### Resultado esperado

Register/login ya guardan usuarios reales.

---

## Paso 1.4 — Empieza P5

### Qué toca

UI de autenticación.

### Archivos que crea o modifica

* `/frontend/src/pages/LoginPage.jsx`
* `/frontend/src/pages/RegisterPage.jsx`
* `/frontend/src/context/AuthContext.jsx`
* `/frontend/src/api/authApi.js`
* `/frontend/src/app/router.jsx`
* `/frontend/src/App.jsx`

### Qué hace

* pantallas login/register
* guardar token
* proteger rutas privadas

### Resultado esperado

Usuario puede iniciar sesión desde frontend.

---

## Paso 1.5 — Empiezan P2, P3 y P4

No hacen todavía su funcionalidad completa; los preparan para usar auth.

---

### P2

#### Archivos que toca

* `/backend/app/modules/sources/schemas.py`
* `/backend/app/modules/sources/models.py`
* `/backend/app/modules/sources/api.py`

#### Qué hace

* preparar `Source` con `created_by` o relación con usuario
* pensar endpoints ya protegidos

---

### P3

#### Archivos que toca

* `/backend/app/modules/news/models.py`
* `/backend/app/modules/news/schemas.py`
* `/backend/app/modules/news/api.py`
* `/backend/app/modules/crawler/service.py`

#### Qué hace

* preparar `News` con relación a `Source`
* dejar claro que crawler luego trabajará con fuentes de usuarios

---

### P4

#### Archivos que toca

* `/backend/app/modules/alerts/models.py`
* `/backend/app/modules/alerts/schemas.py`
* `/backend/app/modules/alerts/api.py`

#### Qué hace

* preparar `Alert` relacionada con `User`

---

## Paso 1.6 — Cierra P1

### Qué toca

Revisión final auth.

### Archivos que modifica

* `/backend/app/api/deps.py`
* `/backend/app/modules/auth/api.py`
* `/backend/app/api/router.py`

### Qué hace

* revisar protección de endpoints
* dejar interfaz de auth estable para todos

---

## Paso 1.7 — Cierra P6

### Qué toca

Validación global del sprint.

### Archivos que puede tocar

* `/docker-compose.yml`
* variables de entorno
* configuración DB

### Qué hace

* probar backend + frontend + DB con auth real
* arreglar cualquier problema de arranque/integración

### Resultado final Sprint 1

Register, login y sesión funcionan.

---

# SPRINT 2 — Gestión de fuentes RSS

## Objetivo real

Permitir crear y gestionar feeds RSS, dejando la base para el crawler del siguiente sprint.

---

## ORDEN EXACTO

## Paso 2.1 — Empieza P2

### Qué toca

Módulo `sources` completo.

### Archivos que modifica

* `/backend/app/modules/sources/models.py`
* `/backend/app/modules/sources/schemas.py`
* `/backend/app/modules/sources/repository.py`
* `/backend/app/modules/sources/service.py`
* `/backend/app/modules/sources/api.py`

### Qué hace

* modelo `Source`
* CRUD completo
* validación de URL
* relación con usuario
* activar/desactivar fuente

### Resultado esperado

Backend de sources terminado.

---

## Paso 2.2 — Sigue P6

### Qué toca

Persistencia de sources.

### Archivos que modifica

* migración de `sources`
* configuración DB si hace falta

### Qué hace

* crear tabla `sources`
* meter constraints útiles

### Resultado esperado

Sources ya persisten de verdad.

---

## Paso 2.3 — Empieza P5

### Qué toca

Pantalla de fuentes.

### Archivos que crea o modifica

* `/frontend/src/pages/SourcesPage.jsx`
* `/frontend/src/api/sourcesApi.js`
* `/frontend/src/components/...` lo que necesite
* `/frontend/src/app/router.jsx`

### Qué hace

* crear vista de listar fuentes
* formulario de alta
* editar/eliminar/desactivar

### Resultado esperado

CRUD de sources desde UI.

---

## Paso 2.4 — Empieza P3

### Qué toca

Preparación de `news` para el siguiente sprint y conexión con sources.

### Archivos que modifica

* `/backend/app/modules/news/models.py`
* `/backend/app/modules/news/schemas.py`
* `/backend/app/modules/news/repository.py`
* `/backend/app/modules/news/service.py`
* `/backend/app/modules/crawler/service.py`

### Qué hace

* definir `News`
* definir cómo luego recibirá `Source`
* dejar clara la estrategia anti-duplicados

### Resultado esperado

`news` queda listo para que el crawler lo use en Sprint 4.

---

## Paso 2.5 — Sigue P4

### Qué toca

Preparar `alerts` para que luego puedan filtrar por fuente si queréis.

### Archivos que modifica

* `/backend/app/modules/alerts/models.py`
* `/backend/app/modules/alerts/schemas.py`

### Qué hace

* dejar preparado que una alerta pueda, si queréis, asociarse opcionalmente a una fuente

### Resultado esperado

No implementa aún matching, pero deja el modelo flexible.

---

## Paso 2.6 — Cierra P1

### Qué toca

Revisión global de backend.

### Archivos que puede tocar

* `/backend/app/api/router.py`
* `/backend/app/api/deps.py`
* `/backend/app/modules/sources/api.py`

### Qué hace

* revisar que `sources` siga el patrón correcto
* revisar auth/permisos
* revisar coherencia general de nombres y respuestas

### Resultado esperado

Módulo `sources` queda limpio y consistente.

---

## Paso 2.7 — Cierra P6

### Qué toca

Integración del sprint.

### Archivos que puede tocar

* `/docker-compose.yml`
* variables entorno
* configuración DB
* seed scripts si hacéis alguno

### Qué hace

* probar flujo completo:

  * login
  * crear source
  * listar sources
* corregir fallos de integración

### Resultado final Sprint 2

El usuario puede gestionar feeds RSS reales.

---

# SPRINT 3 — Gestión de alertas

## Objetivo real

Permitir definir alertas antes de conectar matching y notificaciones en sprints posteriores.

---

## ORDEN EXACTO

## Paso 3.1 — Empieza P4

### Qué toca

Módulo `alerts` completo.

### Archivos que modifica

* `/backend/app/modules/alerts/models.py`
* `/backend/app/modules/alerts/schemas.py`
* `/backend/app/modules/alerts/repository.py`
* `/backend/app/modules/alerts/service.py`
* `/backend/app/modules/alerts/api.py`

### Qué hace

* modelo `Alert`
* CRUD completo
* activar/desactivar
* relación con usuario
* opcional: relación con fuente

### Resultado esperado

Backend de alertas terminado.

---

## Paso 3.2 — Sigue P6

### Qué toca

Persistencia de alerts.

### Archivos que modifica

* migración de `alerts`

### Qué hace

* crear tabla `alerts`
* validar relaciones y constraints

---

## Paso 3.3 — Empieza P5

### Qué toca

Pantalla de alertas.

### Archivos que crea o modifica

* `/frontend/src/pages/AlertsPage.jsx`
* `/frontend/src/api/alertsApi.js`
* `/frontend/src/app/router.jsx`

### Qué hace

* listar alertas
* crear alerta
* editar/eliminar/desactivar

### Resultado esperado

Alertas gestionables desde frontend.

---

## Paso 3.4 — Sigue P3

### Qué toca

Preparar integración futura entre news/crawler y alerts.

### Archivos que modifica

* `/backend/app/modules/crawler/service.py`
* `/backend/app/modules/news/service.py`

### Qué hace

* definir cómo, en sprint siguiente, una noticia nueva llamará a matching
* dejar hueco limpio para esa integración, sin implementarla aún del todo

### Resultado esperado

La conexión futura queda pensada sin acoplar mal las piezas.

---

## Paso 3.5 — Sigue P2

### Qué toca

Apoyo de coherencia entre `sources` y `alerts`.

### Archivos que puede tocar

* `/backend/app/modules/sources/models.py`
* `/backend/app/modules/alerts/models.py`
* `/backend/app/modules/alerts/schemas.py`

### Qué hace

* revisar si la alerta puede filtrar por fuente
* asegurar consistencia entre ambos modelos

---

## Paso 3.6 — Cierra P1

### Qué toca

Revisión arquitectónica del sprint.

### Archivos que puede tocar

* `/backend/app/api/router.py`
* `/backend/app/modules/alerts/api.py`
* `/backend/app/api/deps.py`

### Qué hace

* revisar ownership/permisos
* revisar que no haya lógica metida en endpoints
* revisar coherencia con auth

---

## Paso 3.7 — Cierra P6

### Qué toca

Integración del sprint.

### Qué hace

* probar flujo:

  * login
  * crear source
  * crear alerta
  * listar alerta
* cerrar problemas de DB, entorno o compose

### Resultado final Sprint 3

Usuarios pueden crear alertas listas para usar en matching luego.

---

# SPRINT 4 — Monitorización de noticias

## Objetivo real

Meter **noticias reales en el sistema** desde RSS → DB (base del valor del proyecto) 

---

## ORDEN EXACTO

---

## Paso 4.1 — Empieza P3 (CRÍTICO)

### Qué toca

Crawler completo (pieza central del sistema)

### Archivos que modifica/crea

```
/backend/app/modules/crawler/rss_client.py
/backend/app/modules/crawler/parser.py
/backend/app/modules/crawler/service.py
/backend/app/modules/crawler/scheduler.py
/backend/app/modules/crawler/deduplication.py

/backend/app/modules/news/models.py
/backend/app/modules/news/repository.py
/backend/app/modules/news/service.py
/backend/app/modules/news/schemas.py
```

### Qué debe hacer (MUY ATÓMICO)

1. **RSS Client**

   * hacer fetch HTTP de RSS
   * manejar errores (timeout, invalid XML)

2. **Parser**

   * parsear XML → items
   * extraer:

     * title
     * link
     * description
     * pub_date

3. **Modelo News**

   * campos:

     ```
     id
     title
     content/summary
     url
     published_at
     source_id
     created_at
     ```
   * índice en `url` (clave para deduplicación)

4. **Deduplicación**

   * comprobar si `url` ya existe antes de insertar

5. **Service crawler**

   * flujo:

     ```
     for source in active_sources:
         fetch RSS
         parse items
         for item:
             if not duplicate:
                 save news
     ```

6. **Scheduler**

   * ejecutar cada X minutos (configurable)

---

### Resultado esperado

 Ya hay noticias reales en DB automáticamente

---

## Paso 4.2 — Sigue P6

### Qué toca

Infraestructura del crawler

### Archivos

```
/backend/.env
/docker-compose.yml
```

### Qué hace

* variable:

  ```
  CRAWLER_INTERVAL=300
  ```
* asegurar que el scheduler arranca con FastAPI
* logging del crawler

---

### Resultado

 El crawler se ejecuta solo sin intervención

---

## Paso 4.3 — Empieza P2

### Qué toca

Integración con sources

### Archivos

```
/backend/app/modules/sources/service.py
/backend/app/modules/sources/repository.py
```

### Qué hace

* método:

  ```
  get_active_sources(user_id?)
  ```
* opcional:

  * filtrar por user
  * filtrar por categoría

---

### Resultado

 El crawler usa sources reales del sistema

---

## Paso 4.4 — Empieza P5

### Qué toca

UI de noticias

### Archivos

```
/frontend/src/pages/NewsPage.jsx
/frontend/src/api/newsApi.js
/frontend/src/components/NewsCard.jsx
```

### Qué hace

* listar noticias
* mostrar:

  * título
  * resumen
  * fecha
  * fuente
* paginación básica

---

### Resultado

 Usuario ve noticias reales en frontend

---

## Paso 4.5 — Sigue P4

### Qué toca

Preparar matching

### Archivos

```
/backend/app/modules/alerts/service.py
/backend/app/modules/notifications/service.py
```

### Qué hace

* definir interfaz:

  ```
  match_news_with_alerts(news)
  ```
* NO implementarlo aún

---

### Resultado

 Base limpia para Sprint 5

---

## Paso 4.6 — Cierra P1

### Qué toca

Revisión arquitectura

### Qué revisa

* que crawler NO tenga lógica de alerts
* separación:

  * crawler → news
  * alerts → matching (después)

---

## Paso 4.7 — Cierra P6

### Qué toca

Integración final

### Qué prueba

```
login
crear source
esperar crawler
ver noticias en DB
ver noticias en frontend
```

---

## Resultado Sprint 4

```
RSS → crawler → DB → frontend
```

---

# SPRINT 5 — Notificaciones + API

## Objetivo real

Cerrar el **core funcional completo del sistema**
(alerta → noticia → notificación) 

---

## ORDEN EXACTO

---

## Paso 5.1 — Empieza P4 (CRÍTICO)

### Qué toca

Matching engine

### Archivos

```
/backend/app/modules/alerts/service.py
/backend/app/modules/notifications/service.py
```

### Qué hace (MUY ATÓMICO)

1. función:

   ```
   match_news_with_alerts(news)
   ```

2. lógica:

   ```
   for alert in user_alerts:
       if keyword in news.title or news.content:
           create notification
   ```

3. mejorar matching:

   * lowercase
   * múltiples keywords
   * opcional: regex

---

### Resultado

 Detecta coincidencias

---

## Paso 5.2 — Sigue P4

### Qué toca

Modelo Notification

### Archivos

```
/backend/app/modules/notifications/models.py
/schemas.py
/repository.py
/service.py
/api.py
```

### Modelo

```
id
user_id
alert_id
news_id
title
created_at
read (bool)
```

---

## Paso 5.3 — Sigue P6

### Qué toca

Migración

* tabla `notifications`
* índices:

  * user_id
  * alert_id

---

## Paso 5.4 — Empieza P3

### Qué toca

Integración crawler → matching

### Archivos

```
/backend/app/modules/crawler/service.py
```

### Qué hace

Después de guardar news:

```
match_news_with_alerts(news)
```

---

### Resultado

 Flujo automático completo

---

## Paso 5.5 — Empieza P5

### Qué toca

UI notificaciones

### Archivos

```
/frontend/src/pages/NotificationsPage.jsx
/frontend/src/api/notificationsApi.js
```

### Qué hace

* listar notificaciones
* marcar como leídas
* mostrar:

  * alerta
  * noticia
  * fecha

---

### Resultado

 Usuario ve resultados del sistema

---

## Paso 5.6 — Sigue P1

### Qué toca

Revisión API REST (MUY IMPORTANTE)

Según el enunciado:
 TODO debe estar expuesto vía API 

### Qué revisa

* endpoints consistentes
* auth correcta
* naming limpio

---

## Paso 5.7 — Cierra P6

### Qué toca

Validación completa

### Flujo a probar

```
login
crear source
crear alerta
esperar crawler
generar noticia
matching automático
ver notificación
```

---

## Resultado Sprint 5

```
RSS
→ crawler
→ news
→ matching
→ notifications
→ UI
```

Esto ya es el **producto completo funcional**

---
