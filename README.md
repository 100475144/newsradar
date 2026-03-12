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


