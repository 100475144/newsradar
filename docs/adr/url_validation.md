# ADR — Validación de URLs en endpoints de Source/Channel

Fecha: 2026-05-13
Estado: Aceptado

## Contexto

Los endpoints ``POST /information-sources``, ``PUT /information-sources/{id}``,
``POST /information-sources/{id}/rss-channels`` y
``PUT /information-sources/{id}/rss-channels/{id}`` reciben URLs de feeds
RSS o de homepages de medios y deben validarlas antes de aceptar la
operación.

La implementación original validaba *accesibilidad HTTP completa*
síncrona dentro del request:

```python
def _check_url_accessible(url, timeout=5.0):
    urlopen(HEAD, timeout=5)
    # fallback GET timeout=5
    # ...

def _check_rss_content(url, timeout=10.0):
    for attempt in range(3):
        urlopen(GET, timeout=10)
        time.sleep(1)
    # ...
```

Esta validación tenía dos problemas serios:

1. **Latencia hasta ~32 s** por POST (10 s × 3 reintentos + sleeps en el
   peor caso).
2. **Acoplamiento a infraestructura ajena**: si un host externo aplicaba
   rate-limiting o estaba momentáneamente lento, nuestro endpoint
   absorbía la latencia y a menudo respondía 400 *aunque la URL fuera
   válida*.

Durante la batería de verificación (con ~28 POSTs consecutivos a
``hnrss.org``), el servidor remoto entraba en rate-limit y muchos tests
fallaban con "URL is not accessible" o "timed out" — falsos negativos.

## Decisión

**Separación de responsabilidades** entre el endpoint (valida la *forma*)
y el crawler (valida la *función*):

### En el POST

1. **Pydantic ``HttpUrl``** valida la sintaxis de la URL.
2. **DNS** (``socket.gethostbyname``, ~50 ms) confirma que el hostname
   existe.
3. **HEAD HTTP** con ``timeout=2 s`` y sin retries:
   * Fallo **400** si la conexión se rechaza activamente
     (``ConnectionRefusedError``) o si el servidor responde 4xx.
   * **Tolerar** timeouts, errores SSL, 5xx y demás transitorios.
4. Para canales RSS, **inspección de contenido**: si el body se descarga,
   debe contener ``<rss``, ``<feed`` o ``<rdf``; si no, 400.

Si la URL pasa estos pasos, la fila se persiste y el crawler la
recogerá en su próximo ciclo. Si el feed deja de responder, el crawler
lo refleja en sus logs y marca el canal como inactivo (responsabilidad
del módulo ``crawler``, no del endpoint).

### Lo que NO hacemos en el POST

* Reintentos HTTP.
* Timeouts > 2 s.
* Validar accesibilidad de hosts que **responden lentos** (los toleramos:
  el crawler los reintenta cada 5 min).

## Tests del verificador afectados

| Caso | Resultado | Motivo |
|---|---|---|
| **IS-009** | OK | Host con puerto cerrado → ConnectionRefused → 400. |
| **IS-010** | OK | Dominio inexistente → DNS fail → 400. |
| **IS-024** | OK | Update con URL inaccesible → mismo flujo → 400. |
| **RSS-001 / RSS-013** | OK | ``hnrss.org`` resuelve por DNS y responde rápido → 201. |
| **RSS-008** | OK | URL con dominio inexistente → DNS fail → 400. |
| **RSS-009** | OK | URL responde HTML → no contiene markers RSS → 400. |
| **RSS-010** | OK | URL no devuelve XML → 400. |
| **RSS-015 / 017 / 018 / 026 / 027 / 028** | OK | Si ``hnrss.org`` timeoutea, toleramos → 201 rápido. |
| **GA-023** | OK | Mismo flujo. |

## Consecuencias

* Latencia POST acotada a ~2 s incluso con red Docker → terceros lenta.
* El sistema acepta URLs que están temporalmente caídas pero son válidas
  formalmente. El crawler las detecta luego.
* Mensajes de log más útiles: el crawler dice exactamente *cuándo* y
  *cuántas veces* falla una URL.
* Tests del verificador estables: las URLs ``hnrss.org`` no provocan
  falsos negativos por rate-limiting de un tercero.
