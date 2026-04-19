# Reparto de tareas finales — NEWSRADAR

Este documento recoge lo que queda para cerrar el proyecto con nota máxima y cómo nos repartimos el trabajo. Cada persona trabaja en su propia rama `feature/<nombre>-<tarea>` y abre PR a `main` con review de al menos 1 compañero.

---

## Resumen del reparto

| # | Tarea | Responsable |
|---|---|---|
| 2 | Blindaje `conftest.py` contra BD principal | **Adrian** |
| 3 | CI con GitHub Actions | **Javier** |
| 4a | Tests backend (auth, sources) | **Adrian** |
| 4b | Tests crawler (casos reales + error) | **100475101** |
| 4c | Smoke tests frontend (vitest) | **100475102** |
| 5 | Documentación técnica faltante | **Cristina** |
| 6 | Unificar config crawler en docker-compose | **100475101** |
| 7 | Script/checklist de demo reproducible | **Javier** |
| 8 | Pulir UX (dashboard + ocultar acciones a lector) | **Manso** |
| 9 | `.env.example` en raíz y backend | **Cristina** |

---

## Criterio del reparto

Asignamos cada tarea a quien ya tocó esa zona del código, para aprovechar el contexto y minimizar tiempo de onboarding.

---

## Tareas detalladas

### Adrian (100495924) — Tests seguros y ampliados

**Por qué tú:** ya preparaste la infraestructura de pytest en Docker (Sprint 7 P6). Eres quien mejor conoce el setup.

**#2 — Blindaje `conftest.py`**
1. Abrir `backend/app/tests/conftest.py`.
2. Al inicio, forzar que `DATABASE_URL` apunte a BD de test (ej. `postgresql://.../newsradar_test`).
3. Si la URL contiene el nombre de la BD de producción (`newsradar`) sin sufijo `_test`, lanzar `RuntimeError` y abortar.
4. Documentar el mecanismo en un comentario en cabecera.

**#4a — Tests backend auth + sources**
1. `test_auth.py`: registro, login, verificación de email, login con email no verificado (debe fallar), cambio de rol (admin only), 403 para lector intentando crear alerta.
2. `test_sources.py`: CRUD completo, validación de categoría IPTC, activar/desactivar, 403 para lector en escritura.

**Entregables:** 2 archivos de test + `conftest.py` blindado.

---

### 100475101 — Crawler

**Por qué tú:** eres el "dueño" del crawler desde el Sprint 4.

**#6 — Unificar config**
1. En `docker-compose.yaml` (línea 9) reemplazar `CRAWLER_INTERVAL_SECONDS=300` por `CRAWLER_CRON_EXPRESSION=*/5 * * * *`.
2. Verificar que `backend/app/modules/crawler/scheduler.py` solo lee la nueva variable.
3. Eliminar cualquier referencia muerta a `INTERVAL_SECONDS` si queda en código o docs.

**#4b — Tests crawler**
1. `test_crawler_success.py`: mockear feedparser con un feed válido, verificar que se crean `News` en BD sin duplicar.
2. `test_crawler_errors.py`: feed caído (HTTP 500), feed malformado, feed vacío. En todos los casos el crawler no debe romper.
3. `test_crawler_dedup.py`: mismo feed ejecutado dos veces no crea noticias duplicadas.

**Entregables:** docker-compose actualizado + 3 archivos de test.

---

### 100475102 — Tests frontend

**Por qué tú:** tarea acotada e independiente, buena para entrar con calma.

**#4c — Smoke tests frontend**
1. Instalar en `frontend/`: `npm i -D vitest @testing-library/react @testing-library/jest-dom jsdom`.
2. Añadir script `"test": "vitest"` a `frontend/package.json`.
3. Configurar `vitest.config.js` con entorno `jsdom`.
4. Crear 3 smoke tests:
   - `LoginPage` renderiza los campos email/password.
   - `AlertsPage` renderiza el título y el botón "Nueva alerta".
   - `NewsPage` renderiza el filtro de categoría.

**Entregables:** vitest instalado + configurado + 3 tests pasando.

---

### Cristina (100475144) — Documentación técnica

**Por qué yo:** he tocado casi todos los módulos (auth, alertas, notificaciones, seeds), tengo la visión global.

**#5 — Docs faltantes**
Crear en `docs/`:
1. `architecture.md` — diagrama de módulos, flujo RSS → crawler → news → matching → notificación, decisiones de diseño clave.
2. `api-design.md` — mapa de endpoints por módulo (auth, alerts, sources, news, notifications), formatos request/response, auth requerida por endpoint.
3. `database-design.md` — diagrama ER, descripción de tablas y FKs, estrategia de migraciones Alembic.
4. `extension-guide.md` — "cómo añadir un módulo nuevo", "cómo añadir un canal de notificación", "cómo añadir una categoría IPTC custom".
5. `testing-strategy.md` — niveles de test, comandos, cómo correr el entorno aislado.

**#9 — `.env.example`**
1. `.env.example` en raíz con todas las variables usadas en `docker-compose.yaml`.
2. `backend/.env.example` con las variables de `app/core/config.py` (JWT, SMTP, admin seed, crawler cron).
3. Comentario breve junto a cada variable.

**Entregables:** 5 `.md` nuevos en `docs/` + 2 `.env.example`.

---

### Manso (100474286) — UX

**Por qué tú:** ya hiciste varios fixes de UI, conoces el frontend.

**#8 — Pulir UX**
1. `DashboardPage.jsx`: añadir al menos 3 widgets (contador de alertas activas, últimas 5 noticias, contador de notificaciones no leídas).
2. En `AlertsPage`, `SourcesPage`: leer el rol del usuario desde el contexto de auth. Si es `lector`, ocultar botones de "Crear", "Editar", "Eliminar" en vez de dejar que falle el backend con 403.
3. Mostrar un badge en la sidebar con el rol del usuario (ya parcialmente hecho).

**Entregables:** dashboard mejorado + UX condicionada por rol.

---

### Javier — CI y demo

**Por qué tú:** has hecho muchos PRs, tienes visión transversal; el CI necesita conocer backend + frontend.

**#3 — GitHub Actions CI**
Crear `.github/workflows/ci.yml` con jobs:
1. **backend-test**: levanta Postgres de servicio, instala deps, corre `pytest`.
2. **backend-lint**: `ruff check` sobre `backend/app/`.
3. **frontend-build**: `npm ci` + `npm run build` en `frontend/`.
4. **frontend-test**: `npm test` (depende de que 100475102 haya mergeado vitest antes).

Trigger: push a `main` y PRs.

**#7 — Script de demo**
Crear `docs/demo.md` con checklist paso a paso:
1. Levantar con `docker compose up --build`.
2. Login como `admin@newsradar.com`.
3. Crear fuente RSS.
4. Crear alerta con categoría IPTC y keyword.
5. Esperar al crawler (o forzarlo) y verificar notificación en la UI.
6. Verificar email en MailHog (http://localhost:8025).

Opcionalmente, `scripts/demo.sh` que haga los pasos por API.

**Entregables:** `ci.yml` verde + `demo.md` + opcional `demo.sh`.

---

## Orden de merge recomendado

Para evitar bloqueos:

1. **Primera tanda (en paralelo):** Cristina (#5, #9), Adrian (#2, #4a), 100475101 (#6, #4b), Manso (#8).
2. **Segunda tanda (depende de tests backend ya mergeados):** 100475102 (#4c).
3. **Tercera tanda (depende de todos los tests):** Javier (#3 CI + #7 demo).

---

## Reglas de trabajo

- Una rama por persona: `feature/<nombre>-<tarea>` (ej. `feature/adrian-tests-blindaje`).
- PR a `main` con descripción clara de qué se ha hecho.
- Review mínima de 1 compañero antes de mergear.
- Si tocas archivos de otro, avisa antes por el grupo.
- No hacer push directo a `main`.

---

## Estado actual del proyecto

Sprints 0–5 **completados**. Sprint 6 parcial. Sprints 7–8 pendientes (cubiertos por este reparto). Tras estas tareas, el proyecto queda listo para entrega final.
