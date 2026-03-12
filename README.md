```markdown
# NEWSRADAR

NEWSRADAR is a modular news monitoring system that continuously collects news from RSS sources and alerts users when relevant content appears.

The system allows users to register RSS sources, define keyword-based alerts, and receive notifications when new articles match their interests.

This project is designed with a strong focus on **modularity, maintainability, and adaptability**, allowing the system to evolve quickly and incorporate new features or architectural changes with minimal impact.

---

# System Overview

The system is composed of four main components:

- **Frontend:** React + Vite
- **Backend API:** FastAPI
- **Database:** PostgreSQL
- **Crawler:** internal scheduled task inside the backend

The backend exposes a REST API consumed by the frontend.  
The backend also periodically collects news from external RSS feeds, processes them, and generates alerts when matching user-defined keywords.

---

# High-Level Architecture

```

User
|
v
Frontend (React + Vite)
|
| HTTP / JSON
v
Backend API (FastAPI)
|
| SQL
v
PostgreSQL

Inside Backend:

* Authentication
* Sources management
* News storage
* Alerts system
* Notifications
* RSS crawler & scheduler

```

---

# Key Design Goals

The architecture prioritizes:

- **Modularity**
- **Low coupling between components**
- **Clear separation of responsibilities**
- **Ease of modification**
- **Fast feature iteration**

This design allows the system to adapt quickly to changes such as:

- switching databases
- adding new data sources
- modifying alert logic
- extending notification mechanisms

---

# Project Structure

```

newsradar/
│
├── backend/        FastAPI backend service
├── frontend/       React frontend application
├── docs/           Architecture and project documentation
├── scripts/        Utility scripts for development and deployment
│
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md

```

---

# Technologies Used

| Layer | Technology |
|------|------------|
| Frontend | React + Vite |
| Backend | FastAPI |
| Database | PostgreSQL |
| Containerization | Docker Compose |
| Authentication | JWT |
| Data ingestion | RSS feeds |

---

# Development Philosophy

The system follows a **modular domain-oriented architecture** where each feature is implemented as an independent module.

Backend modules include:

- authentication
- sources
- news
- alerts
- notifications
- crawler

Each module contains:

- API layer
- business logic
- persistence layer
- schemas

This structure enables independent development and reduces cross-module dependencies.

---

# Getting Started

Instructions for running the system will be added as the development progresses.

Future setup will include:

```

docker compose up

```

to start:

- frontend
- backend
- database

---

# Documentation

Technical documentation can be found in the `docs/` directory.

This includes:

- architecture decisions
- API design
- database schema
- deployment guidelines

---

# Team Development Workflow

Development follows a collaborative workflow using:

- GitHub
- pull requests
- code reviews
- modular feature branches

This ensures code quality and maintainability throughout the project lifecycle.
```

---
