Todo el backend FastAPI.

backend/
│
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── router.py
│   │   └── deps.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── database.py
│   │   └── logging_config.py
│   │
│   ├── models/
│   │   └── __init__.py
│   │
│   ├── schemas/
│   │   └── __init__.py
│   │
│   ├── modules/
│   │   ├── auth/
│   │   │   ├── api.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   ├── models.py
│   │   │   └── schemas.py
│   │   │
│   │   ├── users/
│   │   │   ├── api.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   ├── models.py
│   │   │   └── schemas.py
│   │   │
│   │   ├── sources/
│   │   │   ├── api.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   ├── models.py
│   │   │   └── schemas.py
│   │   │
│   │   ├── news/
│   │   │   ├── api.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   ├── models.py
│   │   │   └── schemas.py
│   │   │
│   │   ├── alerts/
│   │   │   ├── api.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   ├── models.py
│   │   │   └── schemas.py
│   │   │
│   │   ├── notifications/
│   │   │   ├── api.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   ├── models.py
│   │   │   └── schemas.py
│   │   │
│   │   └── crawler/
│   │       ├── scheduler.py
│   │       ├── rss_client.py
│   │       ├── parser.py
│   │       ├── service.py
│   │       └── deduplication.py
│   │
│   └── tests/
│       ├── conftest.py
│       ├── test_auth.py
│       ├── test_sources.py
│       ├── test_news.py
│       ├── test_alerts.py
│       └── test_notifications.py
│
├── alembic/
├── alembic.ini
├── requirements.txt
├── Dockerfile
└── .env.example

1. Qué significa cada parte del backend
app/main.py

Punto de entrada de FastAPI.

Contiene:

creación de la app

registro del router principal

eventos de arranque si los necesitáis

configuración básica

app/api/router.py

Router central que junta los routers de todos los módulos.

Ejemplo:

auth router

sources router

news router

alerts router

notifications router

app/api/deps.py

Dependencias compartidas:

usuario autenticado

sesión de base de datos

roles si hubiera

app/core/

Todo lo global.

config.py

Configuración centralizada con variables de entorno.

security.py

JWT, hash de contraseñas, utilidades de auth.

database.py

Conexión a PostgreSQL, engine, session, base declarativa.

logging_config.py

Configuración de logs.

app/modules/

Aquí vive el backend de verdad.

Cada módulo tiene su responsabilidad.

Patrón por módulo

Cada módulo tendrá normalmente:

api.py → endpoints

service.py → lógica de negocio

repository.py → acceso a BD

models.py → modelos ORM

schemas.py → esquemas Pydantic

Este patrón es buenísimo para mantenibilidad.

2. Qué hace cada archivo dentro de un módulo

Voy con un ejemplo, por ejemplo alerts.

alerts/api.py

Define endpoints como:

crear alerta

listar alertas

borrar alerta

editar alerta

Aquí no debe vivir la lógica gorda.

alerts/service.py

Lógica de negocio:

crear alerta

validar reglas

activar/desactivar

coordinar con repository

alerts/repository.py

Acceso a datos:

guardar alerta

buscar alertas del usuario

filtrar alertas activas

Así, si cambia la BD o cambia el ORM, el impacto se reduce.

alerts/models.py

Modelo ORM de la tabla.

alerts/schemas.py

Request/response schemas:

AlertCreate

AlertUpdate

AlertRead
