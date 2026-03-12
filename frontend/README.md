# Frontend Application

The frontend is built with **React and Vite** and provides the user interface for the NEWSRADAR system.

It interacts with the backend through REST API calls.

---

# Responsibilities

The frontend is responsible for:

- user authentication interface
- managing RSS sources
- managing alerts
- displaying news
- displaying notifications
- interacting with the backend API

The frontend **does not implement business logic**. All core logic remains in the backend.

---

# Frontend Structure

```

frontend/
│
├── public/
│
├── src/
│   ├── main.jsx
│   ├── App.jsx
│
│   ├── app/
│   │   ├── router.jsx
│   │   └── providers.jsx
│
│   ├── api/
│   │   ├── client.js
│   │   ├── authApi.js
│   │   ├── sourcesApi.js
│   │   ├── newsApi.js
│   │   ├── alertsApi.js
│   │   └── notificationsApi.js
│
│   ├── features/
│   │   ├── auth/
│   │   ├── sources/
│   │   ├── news/
│   │   ├── alerts/
│   │   └── notifications/
│
│   ├── components/
│   │   ├── common/
│   │   └── layout/
│
│   ├── pages/
│   │   ├── LoginPage.jsx
│   │   ├── DashboardPage.jsx
│   │   ├── SourcesPage.jsx
│   │   ├── AlertsPage.jsx
│   │   ├── NewsPage.jsx
│   │   └── NotificationsPage.jsx
│
│   └── styles/
│
├── package.json
├── vite.config.js
└── README.md

```

---

# API Communication

All API communication is centralized in:

```

src/api/

```

This ensures:

- consistent API handling
- easier backend changes
- improved maintainability
