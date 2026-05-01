# ADR — Diseño del sistema de expansión de palabras clave (sinónimos)

## Contexto

NEWSRADAR permite a los gestores definir alertas sobre descriptores (palabras clave). El enunciado del proyecto establece que una alerta podrá expandir su palabra clave principal **generando entre 3 y 10 palabras extras** (sinónimos u otras palabras relacionadas) para ampliar la cobertura del matching.

El módulo de alertas (`alerts`) necesita, por tanto, un mecanismo que:

1. Reciba una keyword introducida por el usuario.
2. Proponga términos relacionados de forma automática.
3. Garantice que la propuesta contiene entre 3 y 10 sugerencias (nunca menos, nunca más).
4. Permita al usuario aceptar o descartar las sugerencias antes de guardar la alerta.
5. Almacene los términos finalmente aceptados como `descriptors` en el modelo `Alert`.

La arquitectura del proyecto es modular, con separación clara entre responsabilidades. El módulo `alerts` contiene sus propios `models`, `schemas`, `repository`, `service` y `api`, por lo que el recomendador debe encajar como componente interno de ese mismo módulo, sin dependencias externas ni llamadas a APIs de terceros en esta fase.


## Decisión

Se adopta un diseño de expansión de palabras clave con estas características:

1. El recomendador será un módulo propio dentro de `app/modules/alerts/`, separado del servicio y del modelo.
2. La base de conocimiento será un diccionario estático organizado por dominio temático curado manualmente.
3. Se garantizará un mínimo de 3 y un máximo de 10 sugerencias en todas las circunstancias.
4. Los términos aceptados por el usuario se almacenarán como `descriptors` (lista de strings) en el modelo `Alert`.
5. El endpoint de sugerencias se expondrá en la API como ruta auxiliar sin necesidad de crear ni modificar una alerta.
6. La keyword principal de matching (`keyword`) se mantiene como campo interno separado de `descriptors` para preservar la semántica del matching.


## Justificación

### 1. Recomendador como componente interno del módulo alerts

El recomendador no es una funcionalidad independiente del sistema: su única razón de existir es apoyar la creación de alertas. Por ello se sitúa en `app/modules/alerts/recommender.py`, siguiendo el mismo patrón que el resto de componentes del módulo (`repository.py`, `service.py`, `api.py`).

Esto evita crear un módulo nuevo solo para una función auxiliar, mantiene la cohesión del módulo y facilita encontrar el código relacionado en un único lugar.

### 2. Diccionario estático curado como fuente de conocimiento

Se decide no integrar un modelo de lenguaje externo ni una API de sinónimos en esta fase por las siguientes razones:

- El enunciado no exige inteligencia semántica avanzada, sino una expansión funcional entre 3 y 10 términos.
- Un diccionario estático es predecible, testeable y sin latencia.
- La cobertura temática de NEWSRADAR es conocida y acotada (política, economía, tecnología, salud, deportes, medio ambiente, cultura, educación), lo que hace manejable el mantenimiento del diccionario.
- Se evita una dependencia de red en el flujo de creación de alertas.

El diccionario se organiza por dominio con entradas de coincidencia exacta y parcial, lo que cubre la mayoría de los casos de uso sin complejidad adicional.

### 3. Fallback con sufijos genéricos para garantizar el mínimo de 3

Cuando el dominio temático de la keyword no tiene entrada en el diccionario, se completa con sufijos genéricos derivados de la propia keyword (por ejemplo, `"keyword news"`, `"keyword updates"`, `"keyword report"`). Esto garantiza que el contrato de 3-10 sugerencias se cumple siempre, incluyendo keywords muy específicas o técnicas no cubiertas por el diccionario.

### 4. Separación entre `keyword` y `descriptors`

El modelo `Alert` mantiene dos campos diferenciados:

- `keyword`: término principal introducido por el usuario. Campo interno, no expuesto en la API oficial. Se usa directamente en el motor de matching (`matching.py`) como primer término de búsqueda.
- `descriptors`: lista de strings con los términos expandidos que el usuario ha aceptado. Campo oficial del API (`AlertBase`). Puede incluir la keyword original, sus sinónimos aceptados, o una combinación de ambos.

Esta separación permite que el matching funcione correctamente aunque el usuario no acepte ninguna sugerencia (usando solo `keyword`) y que el motor pueda explotar todos los descriptores cuando el usuario sí los acepta.

### 5. Endpoint auxiliar de sugerencias sin modificar el estado

Las sugerencias se exponen mediante un endpoint GET:

```
GET /api/v1/alerts/suggestions/{keyword}
```

Este endpoint es de solo lectura: no crea ni modifica ninguna alerta. El usuario consulta las sugerencias, selecciona las que desea incluir y las envía en el payload de creación o actualización de la alerta. Esto separa claramente la fase de recomendación de la fase de persistencia.

### 6. Validación y deduplicación de descriptors en schemas

El schema `AlertBase` aplica validación sobre la lista de `descriptors` antes de persistir:

- Se eliminan strings vacíos o con solo espacios.
- Se deduplican términos insensibles a mayúsculas (manteniendo el orden de entrada).
- Se respeta el límite máximo del campo (200 caracteres por descriptor).

Esta validación se sitúa en `schemas.py` para que aplique tanto a la creación (`AlertCreate`, `AlertCreateInternal`) como a la actualización (`AlertUpdate`).


## Diseño resultante

### Flujo de uso en la interfaz

```text
usuario introduce keyword
    -> GET /api/v1/alerts/suggestions/{keyword}
    -> recommender.suggest_expanded_keywords(keyword)
    -> búsqueda en diccionario estático (exact + partial match)
    -> fallback con sufijos genéricos si < 3 resultados
    -> devuelve entre 3 y 10 sugerencias
    -> usuario selecciona / descarta sugerencias
    -> POST /api/v1/users/{user_id}/alerts  (con descriptors aceptados)
    -> validación y deduplicación en AlertBase
    -> persistencia en BD como Alert.descriptors (JSONB)
```

### Flujo de matching

```text
Alert.keyword  →  término primario de búsqueda en matching.py
Alert.descriptors  →  términos secundarios de búsqueda en matching.py
    -> _alert_terms(alert) combina keyword + descriptors
    -> any(term in haystack for term in terms)
```

### Estructura de ficheros implicados

```
app/modules/alerts/
├── recommender.py       # Lógica de expansión de keywords
├── models.py            # Alert: keyword (str), descriptors (JSONB)
├── schemas.py           # AlertBase: descriptors validados
├── service.py           # AlertService: crea alertas con descriptors
├── repository.py        # AlertRepository: persiste descriptors
├── matching.py          # _alert_terms: combina keyword + descriptors
└── api.py               # GET /alerts/suggestions/{keyword}
```

### Contrato del endpoint de sugerencias

```
GET /api/v1/alerts/suggestions/{keyword}
Authorization: Bearer <token>

Response 200:
{
  "keyword": "inteligencia artificial",
  "suggestions": [
    "ai", "machine learning", "deep learning",
    "neural networks", "chatbot", "automation"
  ],
  "count": 6
}
```

### Cobertura temática del diccionario estático

El diccionario cubre los siguientes dominios alineados con las categorías IPTC de primer nivel que maneja el sistema:

| Dominio | Ejemplos de keywords cubiertas |
|---------|-------------------------------|
| Tecnología / Ciencia | ai, bitcoin, crypto, cybersecurity, 5g, quantum, cloud, software |
| Salud | covid, vaccine, mental health, cancer, diabetes, nutrition |
| Política / Sociedad | elections, climate, immigration, war, terrorism, human rights, corruption |
| Economía / Empresa | inflation, recession, stock market, oil, trade, real estate |
| Medio ambiente | pollution, deforestation, renewable energy, earthquake, flood |
| Deportes | football, olympics, tennis, basketball, formula 1 |
| Cultura | cinema, music, literature, theater |
| Educación | university, education |

Keywords fuera de estos dominios reciben el fallback de sufijos genéricos (`{keyword} news`, `{keyword} updates`, etc.).


## Consecuencias

- El recomendador es fácilmente extensible: añadir nuevas entradas al diccionario no requiere cambios en la API ni en el modelo.
- Si en el futuro se desea integrar un modelo semántico (embeddings, WordNet, LLM), el punto de extensión es `recommender.py` sin necesidad de modificar otros módulos.
- El diccionario estático no cubre keywords en idiomas distintos al inglés más allá de los términos explícitamente incluidos. Esta limitación es aceptable en la fase actual del proyecto.
- El endpoint de sugerencias no requiere estado: puede cachearse a nivel de API gateway si se detecta alta carga.
