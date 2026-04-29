# Documentation

This directory contains all technical documentation related to the NEWSRADAR
system. It is organised so a new developer (or the professor) can locate any
artifact in under 30 seconds.

## Layout

```
docs/
├── README.md                  ← este fichero
├── REPARTO_FINAL.md           ← estado vivo del proyecto y reparto de tareas
├── architecture.md            ← capas, módulos y decisiones globales (D3)
├── api-design.md              ← contrato REST y traza con la API oficial (D3)
├── database-design.md         ← ER, tablas, FKs, migraciones (D3)
├── extension-guide.md         ← cómo añadir módulos / canales / endpoints (D3)
├── testing-strategy.md        ← niveles de test, comandos, fixtures (D3)
├── demo.md                    ← script de demostración reproducible
├── deployment.md              ← despliegue (Docker Compose)
├── sprints.md                 ← histórico por sprint
├── adr/                       ← Architecture Decision Records (D1)
│   ├── crawler_design.md
│   └── development_env.md
└── diagrams/                  ← diagramas Mermaid (D2)
    ├── architecture.md        ← diagrama de bloques
    ├── sequence-notification.md
    └── deployment.md
```

## Lectura recomendada

1. `architecture.md` — visión global.
2. `diagrams/architecture.md` — bloques renderizados.
3. `api-design.md` — qué endpoints existen y por qué.
4. `database-design.md` — qué tablas hay y cómo se relacionan.
5. `testing-strategy.md` — cómo correr y ampliar la batería de tests.
6. `extension-guide.md` — cómo añadir tu propia funcionalidad.

## Documentos vivos

- `REPARTO_FINAL.md` se actualiza al cierre de cada fase con el estado de
  cada tarea y el cumplimiento del checklist del profesor.
- `demo.md` se valida en cada release (cuando se pasa a `main`).

## Architecture Decision Records (ADR)

`docs/adr/` recoge decisiones arquitectónicas con su contexto y consecuencias.
Sigue la convención de
[Michael Nygard](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions/).
