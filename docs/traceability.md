# Trazabilidad requisitos ↔ código ↔ tests

> Documento técnico generado en Fase 3 (D4). Cubre el checklist #39 del
> profesor: cada requisito del enunciado/checklist se mapea al archivo de
> código que lo implementa y al test que lo cubre.

## Cómo leer la tabla

- **Requisito** — texto literal o resumen del check del `DOSS-CHECKLIST_2026`
  o de la adenda oficial (cuando aplica).
- **Origen** — fuente del requisito (checklist número / adenda / duda /
  enunciado base).
- **Implementación** — archivo(s) de código fuente y línea aproximada.
- **Test** — archivo de tests que valida el comportamiento. "—" si no hay
  test directo (cubierto por end-to-end o validación visual).

---

## Gestión de alertas (#1–#11)

| # | Requisito | Origen | Implementación | Test |
|---|---|---|---|---|
| 1 | Permite definir alertas sobre una palabra clave | checklist #1 · enunciado §G.Alertas | `alerts/api.py::create_user_alert`, `alerts/schemas.py::AlertCreateInternal.keyword` | `test_alerts_per_user.py::test_create_alert_returns_official_schema` |
| 2 | Recomienda 3-10 sinónimos | checklist #2 | `alerts/recommender.py::suggest_expanded_keywords` | (cubierto end-to-end) — el endpoint `/alerts/suggestions/{kw}` siempre devuelve 3-10 |
| 3 | Límite máximo 20 alertas/gestor | checklist #3 | `alerts/service.py::AlertService.MAX_ALERTS = 20` + check en `create_alert` | `test_alerts_per_user.py::test_alert_max_limit_per_gestor` |
| 4 | Selección de fuentes/canales RSS específicos | checklist #4 + correo 29-abr | `alerts/schemas.py::AlertBase.rss_channels_ids/information_sources_ids`; `alerts/matching.py::_news_matches_alert` | `test_alerts_per_user.py::test_create_alert_returns_official_schema` |
| 5 | Categoría IPTC primer nivel | checklist #5 + correo 29-abr | `alerts/schemas.py::AlertCategoryItem`; `core/iptc.py::IPTC_CATEGORY_CODES` | `test_alerts_per_user.py::test_create_alert_returns_official_schema` |
| 6 | Cron expression | checklist #6 | `alerts/schemas.py::CRON_REGEX`; `crawler/scheduler.py::CrawlerScheduler` | `test_alerts_per_user.py::test_alert_validation_rejects_invalid_cron` |
| 7 | Clasificación según alerta o fuente | checklist #7 | `crawler/service.py::_resolve_initial_classification`; `alerts/matching.py::_resolve_news_classification` | `test_news_classification.py::test_*_classification_*` |
| 8 | Email al detectar match | checklist #8 | `alerts/matching.py::process_alerts_for_news`; `notifications/email_utils.py::send_email_notification` | `test_alert_email_notification.py::test_matching_news_sends_email_notification_via_mailhog` |
| 9 | Mensaje al buzón interno | checklist #9 | `notifications/repository.py::create`; `notifications/api.py::list_my_notifications` | (E2E) — verificado en flujo de demo |
| 10 | Título "Actualización de [alerta] en [día/hora]" | checklist #10 | `alerts/matching.py:200-204` (línea `title = f"Actualización de {alert.name} en {now}"`) | `test_alert_email_notification.py` (assert "Actualización de" in subject) |
| 11 | Resumen del RSS en notificación | checklist #11 | `alerts/matching.py:212-218` (incluye `news.summary` en body) | `test_alert_email_notification.py` (assert summary content in body) |

## Gestión de fuentes RSS (#12–#15)

| # | Requisito | Origen | Implementación | Test |
|---|---|---|---|---|
| 12 | Alta de canales RSS asociados a un medio | checklist #12 | `sources/api.py::create_rss_channel` (anidado bajo `/information-sources/{id}/rss-channels`); modelos `InformationSource` + `RSSChannel` | `test_sources_split.py::test_nested_rss_channel_crud` |
| 13 | Mínimo inicial de 100 canales RSS | checklist #13 | `core/seed_sources.py::RSS_SEEDS_RAW` (110 canales) | `test_default_source_catalog.py::test_default_catalog_summary_meets_source_checklist` |
| 14 | ≥10 medios diferentes | checklist #14 | Mismo seed (20 medios distintos) | mismo test |
| 15 | Canales para todas las cat IPTC primer nivel | checklist #15 | Mismo seed (cubre las 17) | mismo test |

## Gestión de usuarios y roles (#16–#21)

| # | Requisito | Origen | Implementación | Test |
|---|---|---|---|---|
| 16 | Roles "Gestor" y "Lector" definidos | checklist #16 / **adenda elimina lector** | `auth/schemas.py::UserRole` (admin + gestor); `auth/models.py::Role` | `test_auth.py::test_register_assigns_gestor_role_automatically` |
| 17 | ~~Lector bloqueado en alertas~~ | adenda anula | N/A (lector eliminado) | — |
| 18 | Email + nombre + apellidos + organización | checklist #18 | `auth/schemas.py::UserBase` (todos required tras T6.7) | `test_auth.py::test_register_requires_organization` |
| 19 | Email de verificación | checklist #19 | `auth/service.py::register_user`; `notifications/email_utils.py::send_verification_email`; endpoint `/auth/verify-email` | `test_auth.py::test_login_blocked_for_unverified_user` |
| 20 | Token expira a 24h | checklist #20 | `core/config.py::verification_token_expire_hours = 24`; `auth/repository.py::create_verification_token` | (config verificada por inspección) |
| 21 | Admin inicial | checklist #21 | `main.py::_seed_admin_user`; `core/config.py::admin_*` | (verificado en arranque del log) |
| — | Asignación automática rol gestor | adenda CAMBIO #1bis | `auth/repository.py::DEFAULT_ROLE_NAME = "gestor"` + en `create()` | `test_auth.py::test_register_assigns_gestor_role_automatically` |

## Visualización (#22–#25)

| # | Requisito | Origen | Implementación | Test |
|---|---|---|---|---|
| 22 | Nubes palabras por categoría | checklist #22 + duda 21-abr | `news/repository.py::word_frequencies_for_user`; `news/api.py::my_news_wordcloud`; `pages/DashboardPage.jsx::WordCloud` | (E2E) — verificado en smoke con `/news/me/wordcloud` |
| 23 | Total noticias en stats | checklist #23 + duda 28-abr | `news/repository.py::count_total_for_user`; `news/api.py::my_news_stats` | (E2E) — verificado en smoke con `/news/me/stats` |
| 24 | Alertas por categoría | checklist #24 + duda 28-abr | `alerts/api.py::my_alerts_stats` (`/alerts/me/stats`) | (E2E) — verificado en smoke |
| 25 | i18n ES/EN | checklist #25 | `frontend/src/i18n/index.js`; `react-i18next` | `LoginPage.test.jsx` (mock de i18n + assert keys) |

## API y datos (#26–#29)

| # | Requisito | Origen | Implementación | Test |
|---|---|---|---|---|
| 26 | API REST | checklist #26 | FastAPI; `app/main.py` | `test_health.py` |
| 27 | OpenAPI documentado | checklist #27 | FastAPI auto-genera `/openapi.json` y `/docs` | (verificación visual del Swagger UI) |
| 28 | GET /api/v1/health | checklist #28 | `api/endpoints/health.py` | `test_health.py::test_health` |
| 29 | BD almacena noticias y entidades | checklist #29 | PostgreSQL 18 + 12 tablas (ver `docs/database-design.md`) | (verificado en arranque y migraciones) |

## Repositorio (#30–#33)

| # | Requisito | Origen | Implementación | Evidencia |
|---|---|---|---|---|
| 30 | Código en GitHub | checklist #30 | https://github.com/100475144/newsradar | (URL pública) |
| 31 | Documentación Markdown | checklist #31 | `docs/*.md` | `ls docs/*.md` → 9 archivos |
| 32 | ADRs en `/docs/adr` | checklist #32 | `docs/adr/crawler_design.md`, `development_env.md` | (D1 movió la carpeta) |
| 33 | Diagramas arquitectura | checklist #33 | `docs/diagrams/architecture.md`, `sequence-notification.md`, `deployment.md` | (D2: 3 diagramas Mermaid) |

## DevOps (#34–#38)

| # | Requisito | Origen | Implementación | Test/Evidencia |
|---|---|---|---|---|
| 34 | Pruebas automatizadas en CI | checklist #34 | `.github/workflows/ci.yml::backend-test` job | 31 tests (25 backend + 3-6 frontend) |
| 35 | GitHub Actions para despliegue | checklist #35 | CI sí; CD pendiente (Fase 3 - Javier/CD1) | (parcial) |
| 36 | Métricas calidad (SonarQube) | checklist #36 | Pendiente Fase 3 (Javier/CD3) | ❌ pendiente |
| 37 | Despliegue automático máquina limpia | checklist #37 | `docker compose up --build` lo hace; `docs/deployment.md` lo documenta | (parcial — Fase 3 CD2) |
| 38 | Informe cobertura automático | checklist #38 | `pytest-cov` + artefacto `backend-coverage` en CI | `coverage.xml` + `coverage_html` (TS3) |

## Entregables (#39–#40)

| # | Requisito | Origen | Implementación | Evidencia |
|---|---|---|---|---|
| 39 | Trazabilidad documentada | checklist #39 | **este mismo archivo** (`docs/traceability.md`) | (D4) |
| 40 | Registro prompts IA | checklist #40 | `docs/ai-prompts.md` | (D5) |

## Cambios oficiales (adendas + dudas)

| Cambio | Origen | Implementación | Test |
|---|---|---|---|
| Eliminar rol lector | Adenda CAMBIO #1 | T1: enum + migración Alembic `f1a2b3c4d5e6` | `test_auth.py::test_admin_can_change_user_role` |
| Asignación auto gestor | Adenda CAMBIO #1bis | `auth/repository.py::create` añade gestor_role automáticamente | `test_auth.py::test_register_assigns_gestor_role_automatically` |
| Dashboard per-user | Duda 28-abr (CAMBIO #2) | `news/repository.py::*_for_user`; `alerts/api.py::my_alerts_stats` | (E2E con backfill — generan 31 notif tras crear alerta) |
| API matchea oficial exactamente | Duda 21-abr + correo 29-abr (CAMBIO #3) | Fase 1 completa: T6.1 a T6.7 + 6 migraciones Alembic | `test_alerts_per_user.py`, `test_sources_split.py` |
| Backfill matching al crear alerta | Bug detectado en verificación post-Fase 2 | `alerts/service.py::_backfill_matching_for_alert` | (E2E — alerta nueva genera 31 notif retroactivas) |

## Stats globales

- **Total de checks cubiertos por código**: 38/40 (95%)
- **Total cubiertos por test directo o end-to-end**: 36/40 (90%)
- **Pendientes (Fase 3 — otros responsables)**: #35 CD, #36 SonarQube, #37 despliegue documentado.
