# Sprint Technical Guide

Documento técnico breve para entender el alcance de los tres primeros sprints y, en particular, qué construye P2 en cada uno.

## Vista General

Los sprints 0, 1 y 2 construyen la base del backend por capas:

1. infraestructura y esqueleto de módulos
2. autenticación y ownership por usuario
3. CRUD completo de fuentes RSS

La regla práctica es simple: Sprint 0 crea la estructura, Sprint 1 la conecta con usuarios, Sprint 2 la vuelve funcional.

---

## Parte 1. Sprint 0 - Preparación de infraestructura

### Objetivo técnico

Dejar el backend, frontend y base modular listos para arrancar sin fricción.

### Alcance de P2

P2 solo crea la base del módulo `sources`:

- `backend/app/modules/sources/api.py`
- `backend/app/modules/sources/service.py`
- `backend/app/modules/sources/repository.py`
- `backend/app/modules/sources/models.py`
- `backend/app/modules/sources/schemas.py`

### Qué debe quedar

- la carpeta `sources` existe
- hay archivos base para separar API, lógica, persistencia, modelo y schemas
- no hay negocio todavía

### Dependencias

P2 depende de que el proyecto ya tenga estructura común y que el backend arranque.

### Resultado esperado

El módulo está preparado para evolucionar sin romper la arquitectura general.

---

## Parte 2. Sprint 1 - Usuarios y autenticación

### Objetivo técnico

Introducir identidad real para que cada recurso pueda pertenecer a un usuario.

### Alcance de P2

P2 adapta `sources` para trabajar con usuario autenticado:

- `Source` queda vinculado a `current_user`
- los schemas ya reflejan ownership
- la API se prepara para rutas protegidas

### Qué debe quedar

- el modelo conoce quién crea la fuente
- la capa API asume autenticación
- no se implementa todavía el CRUD completo

### Dependencias

P2 depende de que auth ya tenga `get_current_user` y un usuario válido en sesión.

### Resultado esperado

`sources` queda listo para operar con ownership por usuario antes de implementar CRUD.

---

## Parte 3. Sprint 2 - Gestión de fuentes RSS

### Objetivo técnico

Convertir `sources` en un módulo funcional para crear, consultar, actualizar y gestionar feeds RSS.

### Alcance de P2

P2 implementa el módulo completo:

- modelo `Source`
- repository
- service
- API REST
- validación de URL RSS
- relación con usuario
- activación y desactivación de fuentes

### Qué debe quedar

- CRUD completo disponible desde backend
- cada usuario solo ve y manipula sus fuentes
- la validación de URL evita entradas inválidas
- la fuente puede desactivarse sin borrarse

### Resultado esperado

El backend ya permite gestionar fuentes RSS de forma consistente y deja lista la base para el crawler del siguiente sprint.

---

## Referencia

Para el detalle completo de orden y responsables, sigue mandando `ROADMAP.md` y `BACKLOG.md`. Esta guía solo concentra la parte técnica de los sprints 0, 1 y 2.