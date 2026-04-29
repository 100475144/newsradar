"""Emparejamiento entre alertas y noticias.

Adaptado al schema oficial (T6.4):
- Las alertas filtran por ``rss_channels_ids`` y/o ``information_sources_ids``
  (strings). Si ambos están vacíos, se usa la ``categories`` (list[{code,label}])
  para matchear por categoría del canal.
- ``descriptors`` y ``keyword`` (interno) se usan como términos de matching
  contra título/resumen/autor de la noticia.
- Se genera notificación + email solo para el propietario de la alerta
  (CAMBIO #2 oficial: dashboard / notificaciones son per-user).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.modules.alerts.models import Alert
from app.modules.news.models import News
from app.modules.notifications.email_utils import send_email_notification
from app.modules.notifications.repository import NotificationRepository
from app.modules.sources.models import Category, RSSChannel


def _normalize(value: str | None) -> str:
    return (value or "").strip().lower()


def _alert_terms(alert: Alert) -> list[str]:
    """Return the list of lowercase terms to match against the news text."""
    terms: list[str] = []
    if alert.keyword:
        terms.append(_normalize(alert.keyword))
    for descriptor in alert.descriptors or []:
        norm = _normalize(descriptor)
        if norm:
            terms.append(norm)

    # Eliminar duplicados manteniendo orden.
    seen: set[str] = set()
    unique: list[str] = []
    for term in terms:
        if term and term not in seen:
            seen.add(term)
            unique.append(term)
    return unique


def _alert_category_codes(alert: Alert) -> set[str]:
    return {
        _normalize(item.get("code"))
        for item in (alert.categories or [])
        if isinstance(item, dict) and item.get("code")
    }


def _news_matches_alert(
    news: News,
    alert: Alert,
    channel: RSSChannel | None,
    channel_category: Category | None,
) -> bool:
    if not alert.is_active:
        return False

    rss_filter = {str(value) for value in (alert.rss_channels_ids or []) if value}
    info_filter = {str(value) for value in (alert.information_sources_ids or []) if value}

    if rss_filter or info_filter:
        if channel is None:
            return False
        channel_id_str = str(channel.id)
        info_id_str = str(channel.information_source_id) if channel.information_source_id else ""

        in_rss = channel_id_str in rss_filter if rss_filter else False
        in_info = info_id_str in info_filter if info_filter else False
        if not (in_rss or in_info):
            return False
    else:
        # Si no hay filtro de canales/medios, usar las categorías de la alerta.
        alert_codes = _alert_category_codes(alert)
        if not alert_codes:
            return False
        if channel_category is None:
            return False
        if _normalize(channel_category.name) not in alert_codes:
            return False

    haystack = " ".join(
        part for part in [news.title, news.summary or "", news.author or ""] if part
    ).lower()

    terms = _alert_terms(alert)
    if not terms:
        # Sin términos no matchea (la alerta tiene que tener al menos un descriptor o keyword).
        return False
    return any(term in haystack for term in terms)


def _resolve_news_classification(
    current_category: str | None,
    current_origin: str | None,
    matching_alerts: list[Alert],
) -> tuple[str | None, str]:
    """Si una alerta hace match, su primera categoría sustituye la del news."""
    normalized_origin = (current_origin or "unknown").strip().lower() or "unknown"
    category_votes: dict[str, tuple[int, int]] = {}

    for alert in matching_alerts:
        codes = _alert_category_codes(alert)
        for code in codes:
            if not code:
                continue
            alert_id = alert.id or 0
            if code in category_votes:
                count, first_alert_id = category_votes[code]
                category_votes[code] = (count + 1, min(first_alert_id, alert_id))
            else:
                category_votes[code] = (1, alert_id)

    if not category_votes:
        return current_category, normalized_origin

    selected_category = min(
        category_votes.keys(),
        key=lambda code: (
            -category_votes[code][0],
            category_votes[code][1],
            code,
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

    channel = None
    channel_category = None
    if news.source_id is not None:
        channel = db.query(RSSChannel).filter(RSSChannel.id == news.source_id).first()
        if channel is not None:
            channel_category = (
                db.query(Category)
                .filter(Category.id == channel.category_id)
                .first()
            )

    matching_alerts = [
        alert
        for alert in alerts
        if _news_matches_alert(news, alert, channel, channel_category)
    ]
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

    medium_name = (
        channel.information_source.name
        if channel and channel.information_source
        else None
    )

    notification_repo = NotificationRepository(db)
    created_count = 0

    for alert in matching_alerts:
        owner = alert.owner
        if owner is None or not owner.is_active or not owner.is_verified:
            continue

        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        title = f"Actualización de {alert.name} en {now}"

        published = (
            news.published_at.strftime("%d/%m/%Y %H:%M")
            if getattr(news, "published_at", None)
            else now
        )
        summary = getattr(news, "summary", None) or "Sin resumen disponible."
        message = (
            f"Fuente: {medium_name or 'Desconocida'}\n"
            f"Fecha: {published}\n"
            f"Título: {news.title}\n\n"
            f"{summary}"
        )

        existing_notification = notification_repo.get_by_delivery_key(
            user_id=owner.id,
            alert_id=alert.id,
            news_id=news.id,
        )

        if existing_notification is not None:
            continue

        if alert.notify_in_app:
            notification = notification_repo.create(
                title=title,
                message=message,
                user_id=owner.id,
                alert_id=alert.id,
                news_id=news.id,
            )
            if notification is not None:
                created_count += 1

        if alert.notify_email and owner.email:
            send_email_notification(
                to_email=owner.email,
                subject=title,
                body=f"{message}\n\nEnlace: {news.link}",
            )

    return created_count
