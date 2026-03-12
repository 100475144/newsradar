# Backend Service

The backend service is implemented using **FastAPI** and is responsible for all core system functionality.

It exposes a REST API consumed by the frontend and handles:

- authentication
- source management
- news ingestion
- alerts processing
- notifications
- RSS crawling

---

# Backend Architecture

The backend follows a **modular architecture** based on domain-driven organization.

Each module contains its own:

- API endpoints
- business logic
- database interaction
- data schemas

This approach improves maintainability and allows features to evolve independently.

---

# Backend Directory Structure

```

backend/
│
├── app/
│   ├── main.py
│
│   ├── api/
│   │   ├── router.py
│   │   └── deps.py
│
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── security.py
│   │   └── logging_config.py
│
│   ├── modules/
│   │   ├── auth/
│   │   ├── users/
│   │   ├── sources/
│   │   ├── news/
│   │   ├── alerts/
│   │   ├── notifications/
│   │   └── crawler/
│
│   └── tests/
│
├── requirements.txt
├── Dockerfile
└── README.md

```

---

# Module Pattern

Each backend module follows this structure:

```

module/
├── api.py
├── service.py
├── repository.py
├── models.py
└── schemas.py

```

### api.py
Defines FastAPI endpoints.

### service.py
Contains business logic and orchestrates system behavior.

### repository.py
Handles database interaction.

### models.py
Defines ORM models.

### schemas.py
Defines request and response validation schemas.

---

# Core Components

## API Layer

Responsible for HTTP endpoints and request validation.

## Service Layer

Contains business rules and application logic.

## Repository Layer

Abstracts database access.

## Core Utilities

Shared utilities such as:

- database configuration
- security utilities
- logging
- application settings

---

# Crawler

The crawler is implemented inside the backend as a scheduled task.

Its responsibilities include:

- fetching RSS feeds
- parsing entries
- storing new articles
- triggering alert matching

This design simplifies deployment and reduces system complexity.

---

# Testing

Backend tests are located in:

```

app/tests/

```

Tests will cover:

- API endpoints
- service logic
- alert matching
- crawler functionality

