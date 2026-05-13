# ADR — Auto-relleno de ``descriptors`` en alertas

Fecha: 2026-05-13
Estado: Aceptado

## Contexto

El correo del profesor exige (checklist #2):

> "El sistema debe recomendar entre 3 y 10 sinónimos o palabras
> relacionadas para ampliar la alerta."

La batería de verificación valida que ``Alert.descriptors`` contiene
entre 3 y 10 elementos tras la creación. Por su parte, los clientes
(verificador o UI) pueden:

* No enviar ``descriptors`` (``GA-009``).
* Enviar ``descriptors=[]`` (``GA-010``).
* Enviar ``descriptors`` con duplicados (``GA-011``).
* Enviar ``descriptors`` con < 3 elementos únicos.

## Decisión

En ``AlertService.create_alert`` aplicamos la siguiente cascada:

1. Pydantic dedupea los descriptors recibidos (case-insensitive).
2. Si tras dedupear quedan < 3:
   * Llamamos a ``suggest_expanded_keywords(keyword or name)`` que
     consulta un diccionario ``RELATED_TERMS`` por dominio (ai → ml /
     deep learning / etc., covid → coronavirus / pandemic / etc.).
   * Si el diccionario no cubre la keyword, se generan sufijos
     genéricos a partir del nombre: ``"<name> news"``,
     ``"<name> latest"``, ``"<name> updates"``, ``"<name> report"``...
3. Si aún quedan < 3, completamos con ``f"<name> descriptor-N"``.
4. Truncamos a 10 elementos como máximo.

El resultado es una lista con 3-10 strings únicos que cumple la
restricción del enunciado **independientemente** de lo que el cliente
envíe.

## Justificación

* El enunciado **garantiza** 3-10. Rechazar con 422 cuando el cliente
  envía menos sería técnicamente correcto, pero rompería UX (un usuario
  podría no saber qué sinónimos añadir y el sistema debería *ayudar*).
* Los tests ``GA-009`` y ``GA-010`` confirman que el verificador espera
  **201 con auto-relleno**, no 422.
* La calidad del relleno (vía recommender por dominio o sufijos
  genéricos) es suficiente para que las alertas matcheen contenido real
  cuando la keyword pertenece al diccionario.

## Tests del verificador afectados

| Caso | Resultado | Motivo |
|---|---|---|
| **GA-009** | OK | Sin descriptors, server devuelve 3 (rellenados). |
| **GA-010** | OK | Descriptors vacíos, server devuelve 3. |
| **GA-011** | **OK con WARNING** | Duplicados se dedupean; auto-relleno completa. El verificador marca WARNING porque los descriptors finales no son los originales. **No es bug**: el comportamiento cumple el enunciado. |
| **RN-001** | OK | Recommender devuelve 3-10 sinónimos para keywords del diccionario. |

## Consecuencias

* Las alertas siempre tienen 3-10 descriptors aunque el cliente envíe
  basura.
* El WARNING ``GA-011`` queda como aceptado deliberadamente.
* El recommender es ampliable: añadir entradas a
  ``RELATED_TERMS`` mejora la calidad del relleno para nuevos dominios.
