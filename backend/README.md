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
