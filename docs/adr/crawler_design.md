# ADR — Crawler Design

## Contexto

NEWSRADAR necesita monitorizar noticias publicadas en canales RSS de medios de comunicación y fuentes oficiales. El sistema debe recoger esas noticias de forma periódica, almacenarlas y dejarlas preparadas para fases posteriores como clasificación, matching con alertas y generación de notificaciones.

La arquitectura del proyecto está diseñada de forma modular, con separación clara entre responsabilidades y con módulos independientes para `sources`, `news`, `alerts`, `notifications` y `crawler`. Además, el README ya define el crawler como una tarea interna programada dentro del backend.


## Decisión

Se adopta un diseño de crawler con estas características:

1. El crawler será un módulo propio dentro del backend, separado del módulo `news`.
2. El crawler consumirá únicamente fuentes RSS registradas y activas.
3. La ejecución será periódica mediante un scheduler configurable.
4. El crawler transformará los ítems RSS en noticias normalizadas antes de persistirlas.
5. La persistencia final de las noticias se realizará a través del dominio `news`.
6. Se aplicará deduplicación antes de guardar cada noticia.
7. La integración con matching se hará mediante una interfaz posterior, sin acoplar el crawler directamente al módulo de alertas en esta fase.

## Justificación

### 1. Separación de responsabilidades

Se separa `crawler` de `news` porque ambos módulos tienen responsabilidades distintas.  
El crawler se encarga de leer feeds, parsear RSS y normalizar datos externos.  
El módulo `news` se encarga de representar y almacenar noticias dentro del sistema.

Esto encaja con la arquitectura modular del proyecto, que busca bajo acoplamiento, facilidad de evolución y módulos con responsabilidades claras.

### 2. Uso de RSS como fuente principal de ingestión

Se toma RSS como mecanismo principal de captura porque el propio enunciado del proyecto se basa en la monitorización de canales RSS de medios y fuentes oficiales. Además, el roadmap de Sprint 4 habla explícitamente de cliente RSS y parser.

Esto reduce complejidad frente a scraping HTML genérico, mejora la estabilidad de la ingestión y permite construir una primera versión funcional más rápido.

### 3. Scheduler interno en backend

Se decide mantener el crawler como tarea interna del backend en lugar de montarlo como servicio independiente desde el inicio. El README del proyecto ya define el crawler como una tarea programada dentro del backend.

Este enfoque simplifica la puesta en marcha inicial, evita infraestructura adicional en una fase temprana y permite avanzar en paralelo con el resto del backend.

### 4. Normalización previa al guardado

Los ítems RSS pueden venir con estructuras heterogéneas según el medio. Por eso se decide normalizar campos antes de persistirlos. La noticia almacenada debe quedar preparada para consulta, matching y futuras notificaciones.

Los campos mínimos que el crawler debe intentar extraer son:
- título
- enlace
- resumen
- fecha de publicación
- fuente
- categoría cuando esté disponible
- identificador externo si el feed lo incluye

Esto es coherente con el flujo del sistema, donde las noticias se almacenan y después se usan para clasificación y notificación.

### 5. Deduplicación en backend

Se decide deduplicar antes de persistir para evitar almacenar múltiples veces la misma noticia cuando:
- el crawler se ejecuta periódicamente
- un feed repite elementos
- distintos feeds publican referencias muy parecidas
- se reprocesa una fuente

La deduplicación seguirá este orden preferente:
1. `external_id` del feed, si existe
2. `link` normalizado
3. hash de contenido con campos estables

Esto ayuda a mantener limpia la base de datos y mejora el comportamiento del flujo posterior.


## Diseño resultante

El flujo previsto queda así:

```text
sources activas
    -> crawler scheduler
    -> fetch RSS
    -> parse items
    -> normalize item
    -> deduplicate
    -> persist in news
    -> future handoff to matching