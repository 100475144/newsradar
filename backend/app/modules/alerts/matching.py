"""Emparejamiento entre alertas y noticias.

Reglas:
- Respeta source_ids: si la alerta tiene fuentes específicas, solo matchea noticias de esas fuentes.
- Clasifica la noticia con la categoría IPTC de la alerta si hay match.
- Genera notificaciones solo para el propietario de la alerta.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.alerts.models import Alert
from app.modules.news.models import News
from app.modules.notifications.email_utils import send_email_notification
from app.modules.notifications.repository import NotificationRepository
from app.modules.sources.models import Source


def _normalize(value: str | None) -> str:
    return (value or "").strip().lower()


def _news_matches_alert(news: News, alert: Alert) -> bool:
    if not alert.is_active:
        return False

    if alert.source_ids and news.source_id not in set(alert.source_ids):
        return False

    haystack = " ".join(
        part for part in [news.title, news.summary or "", news.author or ""] if part
    ).lower()

    keywords = [_normalize(alert.keyword)]
    keywords.extend(_normalize(item) for item in (alert.expanded_keywords or []))
    keywords = [item for item in keywords if item]

    return any(keyword in haystack for keyword in keywords)


def _resolve_news_classification(
    current_category: str | None,
    current_origin: str | None,
    matching_alerts: list[Alert],
) -> tuple[str | None, str]:
    normalized_origin = (current_origin or "unknown").strip().lower() or "unknown"
    category_votes: dict[str, tuple[int, int]] = {}

    for alert in matching_alerts:
        category = (alert.category or "").strip()
        if not category:
            continue

        alert_id = alert.id or 0
        if category in category_votes:
            count, first_alert_id = category_votes[category]
            category_votes[category] = (count + 1, min(first_alert_id, alert_id))
        else:
            category_votes[category] = (1, alert_id)

    if not category_votes:
        return current_category, normalized_origin

    selected_category = min(
        category_votes.keys(),
        key=lambda category: (
            -category_votes[category][0],
            category_votes[category][1],
            category,
        ),
    )
    return selected_category, "alert"


def process_alerts_for_news(db: Session, news: News) -> int:
    alerts = (
        db.query(Alert)
        .filter(Alert.is_active.is_(True))
        .order_by(Alert.id.asc())
        .all()
    )

    if not alerts:
        return 0

    matching_alerts = [alert for alert in alerts if _news_matches_alert(news, alert)]
    if not matching_alerts:
        return 0

    selected_category, classification_origin = _resolve_news_classification(
        current_category=getattr(news, "category", None),
        current_origin=getattr(news, "classification_origin", None),
        matching_alerts=matching_alerts,
    )

    if (
        getattr(news, "category", None) != selected_category
        or getattr(news, "classification_origin", None) != classification_origin
    ):
        news.category = selected_category
        if hasattr(news, "classification_origin"):
            news.classification_origin = classification_origin
        db.add(news)
        db.commit()
        db.refresh(news)

    source_name = None
    if news.source_id is not None:
        source = db.query(Source).filter(Source.id == news.source_id).first()
        source_name = source.name if source else None

    notification_repo = NotificationRepository(db)
    created_count = 0

    for alert in matching_alerts:
        owner = alert.owner
        if owner is None or not owner.is_active or not owner.is_verified:
            continue

        title = f"News match: {alert.name}"
        message = news.title if not source_name else f"{news.title} ({source_name})"

        existing_notification = notification_repo.get_by_delivery_key(
            user_id=owner.id,
            alert_id=alert.id,
            news_id=news.id,
        )

        if alert.notify_in_app and existing_notification is None:
            notification = notification_repo.create(
                title=title,
                message=message,
                user_id=owner.id,
                alert_id=alert.id,
                news_id=news.id,
            )
            if notification is not None:
                created_count += 1

        if alert.notify_email and owner.email and existing_notification is None:
            send_email_notification(
                to_email=owner.email,
                subject=title,
                body=f"{message}\n\n{news.link}",
            )

    return created_count