# Registro de prompts de IA utilizados

> Cumple checklist #40 del `DOSS-CHECKLIST_2026`. Documenta los prompts
> realizados a asistentes de IA durante el desarrollo del proyecto, con
> contexto, propósito y resultado verificable.

## Marco general

- **Modelo principal usado:** Anthropic Claude (Sonnet 4.5 con contexto
  extendido 1M, vía Claude Code CLI).
- **Modo de uso:** "pair-programming" — el asistente lee/edita ficheros del
  repo, ejecuta comandos en bash y propone cambios; cada cambio queda en
  un commit con `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`.
- **Trazabilidad git:** los commits que tienen ese trailer (`git log
  --grep="Co-Authored-By: Claude"`) corresponden a sesiones con IA. El
  resto son commits manuales del equipo.
- **Datos privados:** los prompts NO incluyen secretos del proyecto. Las
  variables sensibles (JWT, SMTP) viven solo en `.env` (no commiteado).

## Prompts por fase

### Fase 0 — adenda oficial + verificaciones

| # | Prompt resumido | Propósito | Resultado |
|---|---|---|---|
| F0.1 | "Implementa Phase 0 completa: T1 (eliminar rol lector), T6.1 (prefijo `/api/v1`), T6.2 (Role como entidad), T7/T9/T10 (verificaciones), TS1 (blindaje conftest)." | Cerrar adenda CAMBIO #1/#1bis y validaciones rápidas. | Commit `cb768f1`: 14 archivos, modelo Role + tabla, migración Alembic, blindaje conftest, fix CI. |
| F0.2 | "Verifica que `recommender.py` siempre devuelve 3-10 términos." | Garantizar checklist #2. | Añadidos 10 sufijos genéricos como fallback en `_GENERIC_SUFFIXES`. |
| F0.3 | "Crea migración Alembic para introducir `roles` + `user_roles` y sembrar admin/gestor." | Soportar `User.role_ids` oficial. | Migración `f1a2b3c4d5e6` con backfill desde `user.role` (string). |

### Fase 1 — alinear API con `main.py` oficial (CAMBIO #3)

| # | Prompt resumido | Propósito | Resultado |
|---|---|---|---|
| F1.1 | "Tras leer el `main.py` que mandó el profe, lista discrepancias con nuestra API." | Auditoría inicial. | Documento de 11 discrepancias mapeadas en `REPARTO_FINAL.md` § CAMBIO #3. |
| F1.2 | "T6.3: split de la tabla `sources` en `categories` + `information_sources` + `rss_channels` con backfill que preserve `news.source_id`." | Cumplir contrato oficial sin perder datos. | Migración `f2b3c4d5e6f7` + nueva API CRUD anidada `/information-sources/{id}/rss-channels`. |
| F1.3 | "T6.4: `Alert` → schema oficial. Renombra `expanded_keywords`→`descriptors`, `category`→`categories[]`, divide `source_ids` en `rss_channels_ids` + `information_sources_ids`." | Cumplir el correo del profesor 29-abr. | Migración `f3c4d5e6f7a8` + `matching.py` reescrito + frontend `AlertsPage` con multi-cat y dual-picker. |
| F1.4 | "T6.5: `Notification` con timestamp + metrics. Mantén title/message internos y exponlos via endpoint `/details`." | El modelo oficial es abstracto. | Migración `f4d5e6f7a8b9` + endpoints anidados oficiales + atajos `/users/me/notifications`. |
| F1.5 | "T6.6: módulo `stats` nuevo." | Endpoint oficial CRUD. | Modelo + migración `f5e6f7a8b9c0` + 5 endpoints. |
| F1.6 | "T6.7: `User` con `organization` obligatoria, password ≥6, CRUD `/users` oficial." | Closing CAMBIO #3. | Migración `f6f7a8b9c0d1` + nuevo `users_api.py`. |

### Fase 2 — dashboard per-user + tests + docs

| # | Prompt resumido | Propósito | Resultado |
|---|---|---|---|
| F2.1 | "T4/T5: dashboard y wordcloud filtrados por las alertas del user logueado (CAMBIO #2)." | Cumplir duda 28-abr. | Endpoints `/news/me/stats`, `/news/me/wordcloud`, `/alerts/me/stats` con subquery sobre `notifications`. |
| F2.2 | "TS2: añade tests backend de auth, sources_split y alerts_per_user con helpers compartidos." | Aumentar cobertura. | +16 tests, helpers en `tests/helpers.py`. |
| F2.3 | "TS3: integra pytest-cov en CI con artefactos." | Checklist #38. | Workflow ampliado, cobertura ~74%. |
| F2.4 | "D2: 3 diagramas Mermaid para checklist #7/#8/#9." | Diagramas en repo. | `docs/diagrams/{architecture,sequence-notification,deployment}.md`. |
| F2.5 | "D3: docs técnicas (architecture, api-design, database-design, extension-guide, testing-strategy)." | Documentar el sistema. | 5 documentos en `docs/`. |
| F2.6 | "D6: `.env.example` para raíz y backend." | Onboarding. | Plantillas con comentarios y sin secretos. |

### Verificación post-Fase 2

| # | Prompt resumido | Propósito | Resultado |
|---|---|---|---|
| V.1 | "Verifica que TODO funciona y matchea la API oficial: arranca docker limpio, prueba cada endpoint con curl, corre tests, checklist 40 puntos uno a uno." | QA exhaustiva antes del merge. | 25/25 tests, 36/40 checks ✅, 2 bugs detectados y arreglados (commit `e60663d`). |
| V.2 | "Bug en CI: `test_alert_email_notification` falla con timeout esperando email en MailHog." | Diagnóstico fallo CI. | Fix `4d40273`: añadir SMTP_HOST/PORT/SENDER al job `backend-test`. |

### Fase 3 — TS4/TS5/D4/D5 (sin CDx)

| # | Prompt resumido | Propósito | Resultado |
|---|---|---|---|
| F3.1 | "TS5: tests del crawler (success / error / dedup) con feedparser mockeado." | Aumentar cobertura del módulo más complejo. | `tests/test_crawler.py` (6 tests) + fix de robustez en `crawler/service.py` (try/except por entry malformado). |
| F3.2 | "TS4: smoke tests frontend con vitest. Setup + 3 tests de páginas clave." | Cumplir checklist #34 también para frontend. | `vitest.config.js` + `src/test/setup.js` + tests de `LoginPage`, `AlertsPage`, `NewsPage`. |
| F3.3 | "D4: trazabilidad requisitos↔código↔tests." | Checklist #39. | Este archivo de docs/traceability.md (40 filas mapeadas). |
| F3.4 | "D5: registro prompts IA." | Checklist #40. | **Este mismo documento**. |

## Convenciones de uso responsable

- **Antes de aceptar un cambio**, se verifica con tests + arranque local.
  Ningún commit con co-author de Claude pasó a `main` sin pasar el CI.
- **No se ha generado código sobre datos sensibles** (claves JWT, contraseñas
  reales). Los `.env.example` solo contienen placeholders.
- **Los tests son reales**: el asistente nunca inventó valores esperados;
  los asserts se ajustaron al comportamiento del código verificado a mano.
- **Las decisiones de diseño** (rol lector eliminado, alertas per-user, API
  oficial estricta, backfill matching) provienen del enunciado/adendas del
  profesor; el asistente solo las implementa, no las elige.

## Cómo localizar quién hizo qué

```bash
# Commits con asistencia de IA (Claude)
git log --grep="Co-Authored-By: Claude" --oneline

# Commits manuales del equipo
git log --invert-grep --grep="Co-Authored-By: Claude" --oneline

# Detalle de un commit concreto
git show <hash>
```

## Limitaciones documentadas

1. El asistente no tiene acceso al "main.py oficial" hasta que el equipo lo
   pega en la conversación; las primeras versiones de la API se hicieron
   con la mejor interpretación posible del enunciado, y luego se realineó
   completamente en Fase 1.
2. Algunos diagnósticos requirieron varios intentos (p. ej. el bug de
   matching no retroactivo al crear alerta se descubrió en la verificación
   post-Fase 2, no durante la implementación inicial).
3. La verificación de la API oficial es **estructural** (paths + schemas);
   los matices semánticos (p. ej. "qué métricas debe contener un Stats
   real") quedan a discreción del equipo y se documentan en
   `docs/api-design.md`.
