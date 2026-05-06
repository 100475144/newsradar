# Demo Script (Manual)

Checklist corto para ejecutar una demo funcional end-to-end de NEWSRADAR.

## 1) Levantar el stack

Desde la raiz del repositorio:

```bash
docker compose up --build
```

Confirma que los servicios quedan arriba:
- API en http://localhost:8000
- UI en http://localhost:5173
- MailHog en http://localhost:8025

## 2) Login como admin

En la UI, inicia sesion con:
- Email: admin@newsradar.com
- Password: la definida en entorno (por defecto: `admin123`, igual que el seed del `main.py` oficial)

Si no funciona, verifica variables `ADMIN_EMAIL` y `ADMIN_PASSWORD` en el backend.

## 3) Crear una fuente RSS

En la seccion de fuentes:
- crear una fuente con una URL RSS valida
- dejarla activa

Ejemplo de URL de prueba:
- https://feeds.bbci.co.uk/news/world/rss.xml

## 4) Crear una alerta

En la seccion de alertas:
- crear alerta con una categoria IPTC
- definir keyword principal
- opcionalmente asociar la alerta a la fuente creada

Ejemplo:
- Categoria: science_technology
- Keyword: ai

## 5) Esperar al crawler (o forzarlo)

Opcion A:
- esperar el intervalo configurado por `CRAWLER_INTERVAL_SECONDS`

Opcion B:
- forzar ejecucion si el endpoint/manual trigger del crawler esta habilitado en el entorno

Validacion esperada:
- se ingesta al menos una noticia
- se genera notificacion para la alerta (si hay match)

## 6) Verificar email en MailHog

Abrir:
- http://localhost:8025

Comprobar:
- existe correo para el usuario
- el asunto y cuerpo referencian la alerta y la noticia asociada

---

## Criterio de demo completada

La demo se considera correcta si se valida el flujo completo:
login -> fuente RSS -> alerta -> noticia procesada -> notificacion UI -> email en MailHog.
