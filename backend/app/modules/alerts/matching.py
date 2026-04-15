"""Emparejamiento entre alertas y noticias.

Mejoras:
- Respeta source_ids: si la alerta tiene fuentes específicas, solo matchea noticias de esas fuentes.
- Clasifica la noticia con la categoría IPTC de la alerta si hay match.
"""

from datetime import datetime, timezone

from app.modules.alerts.models import Alert
from app.modules.alerts.repository import AlertRepository
from app.modules.auth.models import User
from app.modules.notifications.email_utils import send_email_notification
from app.modules.notifications.repository import NotificationRepository


def _build_news_text(news) -> str:
    parts = [
        getattr(news, "title", "") or "",
        getattr(news, "summary", "") or "",
        getattr(news, "category", "") or "",
        getattr(news, "author", "") or "",
    ]
    return " ".join(parts).lower().strip()


def _build_terms(alert: Alert) -> list[str]:
    terms = [alert.keyword]
    terms.extend(alert.expanded_keywords or [])
    cleaned = []
    seen = set()

    for term in terms:
        term = (term or "").strip().lower()
        if term and term not in seen:
            seen.add(term)
            cleaned.append(term)

    return cleaned


def _matches(alert: Alert, news, news_text: str) -> bool:
    # Check source_ids filter: if alert specifies sources, only match those
    alert_source_ids = alert.source_ids or []
    if alert_source_ids:
        news_source_id = getattr(news, "source_id", None)
        if news_source_id not in alert_source_ids:
            return False

    terms = _build_terms(alert)
    return any(term in news_text for term in terms)


def _build_notification_title(alert: Alert) -> str:
    now = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M")
    return f"Actualización de {alert.name} en {now}"


def _build_notification_message(alert: Alert, news) -> str:
    source = getattr(news, "source_id", "unknown")
    published_at = getattr(news, "published_at", None)
    published_at_text = published_at.isoformat() if published_at else "unknown"
    title = getattr(news, "title", "")
    summary = getattr(news, "summary", "") or ""
    link = getattr(news, "link", "") or ""

    return (
        f"Alerta: {alert.name}\n"
        f"Categoría: {alert.category}\n"
        f"Origen de la noticia: {source}\n"
        f"Fecha/hora: {published_at_text}\n"
        f"Título: {title}\n"
        f"Resumen: {summary}\n"
        f"Enlace: {link}"
    )


def process_alerts_for_news(db, news) -> int:
    news_text = _build_news_text(news)
    if not news_text:
        return 0

    alert_repo = AlertRepository(db)
    notification_repo = NotificationRepository(db)

    alerts = alert_repo.list_active()
    created = 0

    for alert in alerts:
        if not _matches(alert, news, news_text):
            continue

        # Classify news with alert's IPTC category if news has no category
        if not getattr(news, "category", None) and alert.category:
            news.category = alert.category
            db.add(news)
            db.commit()
            db.refresh(news)

        title = _build_notification_title(alert)
        message = _build_notification_message(alert, news)

        if alert.notify_in_app:
            notification_repo.create(
                title=title,
                message=message,
                created_by=alert.created_by,
            )

        if alert.notify_email:
            user = db.query(User).filter(User.id == alert.created_by).first()
            if user and getattr(user, "email", None):
                send_email_notification(
                    to_email=user.email,
                    subject=title,
                    body=message,
                )

        created += 1

    return created
