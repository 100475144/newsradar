"""Servicio del módulo alerts.

Adaptado al schema oficial (T6.4).
"""

import logging

from fastapi import HTTPException, status

from app.core.iptc import IPTC_CATEGORIES
from app.modules.alerts.models import Alert
from app.modules.alerts.recommender import suggest_expanded_keywords
from app.modules.alerts.repository import AlertRepository

logger = logging.getLogger(__name__)


def _backfill_matching_for_alert(db_session, alert: Alert, *, lookback: int = 500) -> int:
    """Ejecuta el motor de matching contra las últimas ``lookback`` noticias
    para que una alerta recién creada/actualizada genere notificaciones también
    para news pre-existentes (no solo para las que el crawler capture en el
    futuro).

    Devuelve el número de notificaciones creadas.
    """
    from app.modules.alerts.matching import (
        _news_matches_alert,
        _resolve_news_classification,
    )
    from app.modules.notifications.email_utils import send_email_notification
    from app.modules.notifications.repository import NotificationRepository
    from app.modules.notifications.service import build_default_metrics
    from app.modules.news.models import News
    from app.modules.sources.models import Category, RSSChannel
    from datetime import datetime, timezone

    if not alert.is_active:
        return 0

    news_rows = (
        db_session.query(News)
        .order_by(News.published_at.desc().nullslast(), News.id.desc())
        .limit(lookback)
        .all()
    )
    if not news_rows:
        return 0

    notification_repo = NotificationRepository(db_session)
    owner = alert.owner
    if owner is None or not owner.is_active or not owner.is_verified:
        return 0

    created = 0
    for news in news_rows:
        channel = None
        channel_category = None
        if news.source_id is not None:
            channel = (
                db_session.query(RSSChannel)
                .filter(RSSChannel.id == news.source_id)
                .first()
            )
            if channel is not None:
                channel_category = (
                    db_session.query(Category)
                    .filter(Category.id == channel.category_id)
                    .first()
                )

        if not _news_matches_alert(news, alert, channel, channel_category):
            continue

        # Reusar la lógica de classification de matching.py.
        selected_category, classification_origin = _resolve_news_classification(
            current_category=getattr(news, "category", None),
            current_origin=getattr(news, "classification_origin", None),
            matching_alerts=[alert],
        )
        if (
            getattr(news, "category", None) != selected_category
            or getattr(news, "classification_origin", None) != classification_origin
        ):
            news.category = selected_category
            if hasattr(news, "classification_origin"):
                news.classification_origin = classification_origin
            db_session.add(news)
            db_session.commit()
            db_session.refresh(news)

        medium_name = (
            channel.information_source.name
            if channel and channel.information_source
            else None
        )
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

        if notification_repo.get_by_delivery_key(
            user_id=owner.id, alert_id=alert.id, news_id=news.id,
        ):
            continue

        notif_metrics = build_default_metrics(news, medium_name)
        notif_timestamp = (
            getattr(news, "published_at", None) or datetime.now(timezone.utc)
        )

        if alert.notify_in_app:
            notification = notification_repo.create(
                title=title,
                message=message,
                user_id=owner.id,
                alert_id=alert.id,
                news_id=news.id,
                timestamp=notif_timestamp,
                metrics=notif_metrics,
            )
            if notification is not None:
                created += 1

        if alert.notify_email and owner.email:
            send_email_notification(
                to_email=owner.email,
                subject=title,
                body=f"{message}\n\nEnlace: {news.link}",
            )

    if created:
        logger.info("Backfill matching for alert %s created %d notifications", alert.id, created)
    return created


def _normalize_categories(categories: list) -> list[dict]:
    """Normalize and validate categories against the IPTC catalog."""
    cleaned: list[dict] = []
    seen: set[str] = set()
    for entry in categories or []:
        if hasattr(entry, "model_dump"):
            data = entry.model_dump()
        elif isinstance(entry, dict):
            data = entry
        else:
            continue
        code = (data.get("code") or "").strip()
        if not code or code in seen:
            continue
        # Validate code exists in IPTC catalog.
        if code not in IPTC_CATEGORIES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category code '{code}' is not a valid IPTC code.",
            )
        # Validate label matches the catalog name for this code.
        label = (data.get("label") or "").strip()
        expected_label = IPTC_CATEGORIES[code]
        if label and label.lower() != expected_label.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category label '{label}' does not match IPTC code '{code}' (expected '{expected_label}').",
            )
        seen.add(code)
        cleaned.append({"code": code, "label": expected_label})
    return cleaned


def _normalize_id_list(values: list) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for value in values or []:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        cleaned.append(text)
    return cleaned


class AlertService:
    MAX_ALERTS = 20

    def __init__(self, repository: AlertRepository):
        self.repository = repository

    def list_alerts_for_user(self, user_id: int):
        return self.repository.list_for_user(user_id)

    def list_active_alerts(self) -> list[Alert]:
        return self.repository.list_active()

    def get_alert(self, alert_id: int, user_id: int) -> Alert:
        alert = self.repository.get_by_id_for_user(alert_id, user_id)
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found.",
            )
        return alert

    def create_alert(self, data, user_id: int) -> Alert:
        if self.repository.count_for_user(user_id) >= self.MAX_ALERTS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A manager can only create up to 20 alerts.",
            )

        # Enforce max 1 category per alert.
        categories = _normalize_categories(data.categories or [])
        if len(data.categories or []) > 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An alert can have at most one category.",
            )

        # Enforce name uniqueness per user (case-insensitive).
        name = data.name.strip()
        existing_alerts = self.repository.list_for_user(user_id)
        for existing in existing_alerts:
            if existing.name.strip().lower() == name.lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="An alert with this name already exists for this user.",
                )

        # Ensure descriptors has 3-10 items (use recommender if needed).
        descriptors = list(data.descriptors or [])
        if len(descriptors) < 3:
            keyword = getattr(data, "keyword", None) or name
            try:
                suggestions = suggest_expanded_keywords(keyword)
                for s in suggestions:
                    if s not in [d.lower() for d in descriptors] and len(descriptors) < 10:
                        descriptors.append(s)
            except Exception:
                pass
            # Ensure at least 3.
            while len(descriptors) < 3:
                descriptors.append(f"{name} descriptor-{len(descriptors) + 1}")
        descriptors = descriptors[:10]

        alert = self.repository.create(
            name=name,
            descriptors=descriptors,
            categories=categories,
            rss_channels_ids=_normalize_id_list(data.rss_channels_ids or []),
            information_sources_ids=_normalize_id_list(data.information_sources_ids or []),
            cron_expression=data.cron_expression,
            user_id=user_id,
            keyword=getattr(data, "keyword", None),
            notify_in_app=bool(getattr(data, "notify_in_app", True)),
            notify_email=bool(getattr(data, "notify_email", False)),
            is_active=True,
        )
        # Generar notificaciones para news pre-existentes que matcheen.
        try:
            _backfill_matching_for_alert(self.repository.db, alert)
        except Exception:
            logger.exception("Backfill matching failed for alert %s", alert.id)
        return alert

    def update_alert(self, alert_id: int, data, user_id: int) -> Alert:
        alert = self.get_alert(alert_id, user_id)

        fields: dict = {}
        if getattr(data, "name", None) is not None:
            fields["name"] = data.name.strip()
        if getattr(data, "descriptors", None) is not None:
            fields["descriptors"] = list(data.descriptors)
        if getattr(data, "categories", None) is not None:
            fields["categories"] = _normalize_categories(data.categories)
        if getattr(data, "rss_channels_ids", None) is not None:
            fields["rss_channels_ids"] = _normalize_id_list(data.rss_channels_ids)
        if getattr(data, "information_sources_ids", None) is not None:
            fields["information_sources_ids"] = _normalize_id_list(
                data.information_sources_ids
            )
        if getattr(data, "cron_expression", None) is not None:
            fields["cron_expression"] = data.cron_expression
        if getattr(data, "keyword", None) is not None:
            fields["keyword"] = data.keyword
        if getattr(data, "notify_in_app", None) is not None:
            fields["notify_in_app"] = bool(data.notify_in_app)
        if getattr(data, "notify_email", None) is not None:
            fields["notify_email"] = bool(data.notify_email)
        if getattr(data, "is_active", None) is not None:
            fields["is_active"] = bool(data.is_active)

        return self.repository.update(alert, **fields)

    def activate_alert(self, alert_id: int, user_id: int) -> Alert:
        alert = self.get_alert(alert_id, user_id)
        updated = self.repository.update(alert, is_active=True)
        # Activar también dispara backfill (matching contra news existentes).
        try:
            _backfill_matching_for_alert(self.repository.db, updated)
        except Exception:
            logger.exception("Backfill matching failed for alert %s", updated.id)
        return updated

    def deactivate_alert(self, alert_id: int, user_id: int) -> Alert:
        alert = self.get_alert(alert_id, user_id)
        return self.repository.update(alert, is_active=False)

    def delete_alert(self, alert_id: int, user_id: int) -> None:
        alert = self.get_alert(alert_id, user_id)
        self.repository.delete(alert)
