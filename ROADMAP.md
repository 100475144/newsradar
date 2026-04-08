
| Sprint       | Objetivo                       | Estado      |
| ------------ | ------------------------------ |-------------|
| Sprint 0     | Preparación de infraestructura | [completed] |
| Sprint 1     | Usuarios y autenticación       | [completed] |
| Sprint 2     | Gestión de fuentes RSS         | [completed] |
| Sprint 3     | Gestión de alertas             | [ongoing]   |
| Sprint 4     | Monitorización de noticias     | [ongoing]   |
| Sprint 5     | Notificaciones + API REST      |             |
| Sprint 6     | Dashboard y visualización      |             |
| Sprint 7     | Testing, CI/CD, calidad        |             |
| Sprint 8     | Documentación                  |             |
| Verificación | Pruebas finales                |             |


Personas:

**P1 — Arquitectura + Auth**
**P2 — Sources**
**P3 — News + Crawler**
**P4 — Alerts + Matching + Notifications**
**P5 — Frontend**
**P6 — Infraestructura + DB + Testing + CI**


---

# SPRINT 0 — Preparación de infraestructura

### Objetivo

Dejar el proyecto listo para que todos puedan empezar a programar sin problemas.

---

### P6 — Infraestructura

**Qué hace**

* terminar `docker-compose`
* configurar PostgreSQL
* conectar backend con DB
* comprobar que todo levanta con `docker compose up`

**Explicación simple**

> Básicamente deja todo listo para que cualquiera clone el repo y el proyecto funcione.

---

### P1 — Base backend

**Qué hace**

* crear `FastAPI app`
* `main.py`
* router principal
* endpoint `/health`
* config básica

**Explicación simple**

> Deja el backend arrancando aunque todavía no haga nada útil.

---

### P5 — Base frontend

**Qué hace**

* inicializar React + Vite
* crear layout básico
* conectar frontend con `/health`

**Explicación simple**

> Deja el frontend funcionando y comprobando que el backend responde.

---

### P2, P3, P4 — Estructura de módulos

Cada uno crea su módulo vacío:

P2

```
modules/sources
```

P3

```
modules/news
modules/crawler
```

P4

```
modules/alerts
modules/notifications
```

**Explicación simple**

> Solo crean carpetas y archivos base para empezar luego.

---

✅ Resultado Sprint 0

* proyecto arranca
* frontend y backend conectan
* base de datos lista
* estructura modular creada

---

# SPRINT 1 — Usuarios y autenticación

### Objetivo

Cerrar login y registro para que todo lo demás use usuarios reales.

---

### P1 — Auth completo

**Qué hace**

* modelo `User`
* registro
* login
* JWT
* endpoint `/me`
* proteger endpoints

**Explicación simple**

> Hace todo el sistema de login.

---

### P6 — Soporte base de datos

**Qué hace**

* migración de `users`
* setup migraciones
* verificar conexión DB

**Explicación simple**

> Se asegura de que las tablas se creen bien.

---

### P5 — UI de login

**Qué hace**

* página login
* página register
* guardar token
* proteger rutas privadas

**Explicación simple**

> Hace las pantallas para iniciar sesión.

---

### P2, P3, P4

Adaptan sus módulos para asumir:

```
current_user
```

**Explicación simple**

> Preparan sus módulos para que funcionen con usuarios.

---

✅ Resultado Sprint 1

* usuarios pueden registrarse
* login funciona
* frontend usa auth

---

# SPRINT 2 — Gestión de fuentes RSS

### Objetivo

Permitir añadir y gestionar feeds RSS.

---

### P2 — Sources completo

**Qué hace**

* modelo `Source`
* CRUD de fuentes
* validar URL RSS

Endpoints:

```
POST /sources
GET /sources
PUT /sources
DELETE /sources
```

**Explicación simple**

> Hace la parte donde el usuario añade feeds RSS.

---

### P6 — Migraciones

**Qué hace**

* tabla `sources`
* constraints

---

### P5 — UI Sources

**Qué hace**

* página fuentes
* añadir fuente
* editar fuente
* eliminar fuente

---

### P1 — Revisión backend

**Qué hace**

* revisar endpoints
* seguridad
* coherencia

---

### P3 — Preparar integración crawler

**Qué hace**

* preparar función que leerá sources activas

---

### P4

Nada grande todavía.

---

✅ Resultado Sprint 2

El usuario puede:

* añadir RSS
* ver fuentes guardadas

---

# SPRINT 3 — Gestión de alertas

### Objetivo

Permitir al usuario crear alertas.

---

### P4 — Alerts completo

**Qué hace**

* modelo `Alert`
* CRUD alertas
* alertas activas/inactivas

**Explicación simple**

> Permite decir “avísame cuando salga una noticia sobre X”.

---

### P6 — Migración

Tabla:

```
alerts
```

---

### P5 — UI Alerts

**Qué hace**

* página alertas
* crear alerta
* editar alerta
* eliminar alerta

---

### P1

Revisión de permisos.

---

### P3

Prepara interfaz para matching.

---

✅ Resultado Sprint 3

Usuarios pueden crear alertas.

---

# SPRINT 4 — Monitorización de noticias

### Objetivo

Meter noticias reales en el sistema.

---

### P3 — Crawler completo

**Qué hace**

* cliente RSS
* parser
* scheduler
* leer feeds
* guardar noticias
* evitar duplicados

**Explicación simple**

> Hace el robot que va leyendo noticias automáticamente.

---

### P2

Integración con `sources`.

---

### P6

Configura intervalo del crawler.

---

### P5 — UI noticias

Página para listar noticias.

---

### P4

Prepara matching.

---

✅ Resultado Sprint 4

Flujo:

```
RSS -> crawler -> news database
```

---

# SPRINT 5 — Notificaciones + API

### Objetivo

Cerrar el valor principal del sistema.

---

### P4 — Matching

**Qué hace**

* comparar alertas con noticias
* buscar keywords
* generar notificaciones

**Explicación simple**

> Detecta si una noticia coincide con una alerta.

---

### P3

Integra crawler con matching.

---

### P4 — Notifications

Modelo:

```
Notification
```

---

### P5 — UI Notifications

Página de notificaciones.

---

### P6

Migración `notifications`.

---

### P1

Revisión backend.

---

✅ Resultado Sprint 5

Flujo completo:

```
RSS
 -> crawler
 -> news
 -> matching
 -> notifications
```

---

# SPRINT 6 — Dashboard

### Objetivo

Dejar una interfaz decente para usar el sistema.

---

### P5 — Dashboard

Pantallas:

* noticias
* alertas
* fuentes
* notificaciones

**Explicación simple**

> Hace que todo lo anterior se pueda usar fácil desde el navegador.

---

### Backend (P1-P4)

Pequeños ajustes API.

---

### P6

Mejora Docker si hace falta.

---

# SPRINT 7 — Testing y calidad

### Objetivo

Asegurar que el sistema es robusto.

---

### P1

tests auth

### P2

tests sources

### P3

tests crawler/news

### P4

tests alerts/matching

### P6

infraestructura de testing

### P5

pruebas manuales UI

---

# SPRINT 8 — Documentación

Como dijiste:

> cada uno documenta lo suyo.

### P1

documenta auth + arquitectura backend

### P2

documenta sources

### P3

documenta crawler

### P4

documenta alerts y matching

### P5

documenta frontend

### P6

documenta despliegue

---

# Verificación final

Todos prueban el flujo completo:

1. register
2. login
3. crear source
4. crear alerta
5. ejecutar crawler
6. guardar noticias
7. generar notificación
8. ver notificación en UI

---

# Resultado

Con este plan:

* sigue **exactamente vuestra planificación**
* los **6 trabajan en paralelo**
* cada uno tiene **ownership claro**
* la arquitectura **sigue siendo modular**
* los cambios futuros serán **muy rápidos**

---

