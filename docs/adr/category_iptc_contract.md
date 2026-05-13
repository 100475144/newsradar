# ADR — Contrato del recurso ``Category`` (catálogo IPTC cerrado)

Fecha: 2026-05-13
Estado: Aceptado

## Contexto

El sistema clasifica noticias mediante las **17 categorías de primer
nivel del esquema IPTC Media Topics**, especificadas en el correo del
profesor del 13/05/2026 con `id` numérico y `name` canónico en español:

```
01000000 — Artes, cultura, entretenimiento y medios
02000000 — Policía y justicia
03000000 — Catástrofes y accidentes
04000000 — Economía, negocios y finanzas
05000000 — Educación
06000000 — Medio ambiente
07000000 — Salud
08000000 — Interés humano, animales, insólito
09000000 — Mano de obra
10000000 — Estilo de vida y tiempo libre
11000000 — Política
12000000 — Religión y culto
13000000 — Ciencia y tecnología
14000000 — Sociedad
15000000 — Deporte
16000000 — Conflicto, guerra y paz
17000000 — Meteorología
```

Reglas del enunciado:

* **Catálogo cerrado**: solo estos 17 nombres son válidos. Cualquier
  otro nombre se rechaza con 400.
* Si el ``name`` está en el catálogo, **el sistema asigna automáticamente**
  el ``id`` oficial correspondiente.
* El campo ``source`` debe ser siempre ``"IPTC"``.

## Decisiones

### D1. ``Category.id`` se expone como **entero**

El ``id`` es un entero numérico (``1000000`` para "Artes, cultura,
entretenimiento y medios", ``13000000`` para "Ciencia y tecnología"...).

**Justificación**:
* Coherencia interna: todos los recursos del sistema exponen ``id`` como
  entero (``User``, ``Role``, ``InformationSource``, ``RSSChannel``,
  ``Alert``, ``Notification``, ``Stats``). Romper esa simetría sólo para
  ``Category`` introduce inconsistencia para los clientes del API.
* SQLAlchemy almacena el código como entero para indexación eficiente y
  FK desde ``rss_channels``.

### D2. ``POST /categories`` es **idempotente** sobre el catálogo cerrado

Como el catálogo es **fijo, cerrado y de tamaño 17**, sembrado al
arrancar el sistema, un POST con un nombre del catálogo no "crea" una
fila nueva: devuelve la **fila canónica existente** con 201.

**Justificación arquitectónica**:
* En un catálogo cerrado no existe el concepto de "duplicar": el
  cliente no puede introducir un nombre nuevo (lo rechazamos con 400) y
  los 17 nombres válidos están siempre presentes.
* La semántica REST de "ensure exists" devuelve la representación
  canónica, sin ambigüedad. Esto facilita los patrones create-or-get de
  cualquier cliente.
* Devolver 409 al postear un nombre del catálogo sería **engañoso**:
  implicaría que el cliente podría "crear" una nueva fila si no
  existiera, lo cual contradice la regla "catálogo cerrado de 17" del
  enunciado.

**No mantenemos estado en memoria** para diferenciar el "primer POST"
del "segundo POST" — esa sería una solución frágil (no persiste tras
reiniciar, diverge entre workers) y semánticamente confusa.

## Tests del verificador afectados por estas decisiones

| Caso | Resultado | Motivo |
|---|---|---|
| **SMOKE-005** | **NOK justificado** | Espera ``id`` como string padded ``"01000000"``. Decisión D1: ``id`` es entero. **Incompatible con GC-016 (que sí espera entero)** — los dos casos son mutuamente excluyentes en el verificador. |
| **GC-008** | **NOK justificado** | Espera 4xx ante "name-source inconsistente". Con catálogo cerrado D2 + ``source`` obligatorio ``"IPTC"`` el concepto de "inconsistencia name-source" no existe en nuestra spec. |
| **GC-009** | **NOK justificado** | Espera 409 al postear el mismo nombre dos veces. Decisión D2: catálogo cerrado idempotente → siempre 201 con la fila canónica. |
| **GC-010** | **NOK justificado** | Idem GC-009, case-insensitive. |
| **GC-016** | OK | ``id`` se expone como entero (D1). |
| **GC-001** | OK | POST idempotente devuelve 201 con la fila canónica (D2). |
| **GC-022** | OK | 17 categorías sembradas siempre. |

## Coste asumido y razón

Aceptamos 4 NOK (SMOKE-005, GC-008, GC-009, GC-010) a cambio de:
* Código sin estado en memoria global.
* Contrato REST coherente y defendible.
* Sin "trucos" para satisfacer expectativas contradictorias del verificador.

Esta es una aplicación directa de la guía del profesor del 11/05/2026
("de manera excepcional, se podría no pasar algún caso de prueba si
está justificado por alguna regla de negocio más estricta o alguna
cuestión muy particular del equipo").
