"""Servicio de notifications adaptado al schema oficial (T6.5)."""

from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.modules.notifications.repository import NotificationRepository


def _normalize_metrics(metrics) -> list[dict]:
    cleaned: list[dict] = []
    for entry in metrics or []:
        if hasattr(entry, "model_dump"):
            data = entry.model_dump()
        elif isinstance(entry, dict):
            data = entry
        else:
            continue
        name = (data.get("name") or "").strip()
        value = data.get("value")
        if not name or value is None:
            continue
        try:
            value = float(value)
        except (TypeError, ValueError):
            continue
        cleaned.append({"name": name, "value": value})
    return cleaned


class NotificationService:
    def __init__(self, repository: NotificationRepository):
        self.repository = repository

    # ── API canónica (anidada) ───────────────────────────────────────

    def create_for_alert(
        self,
        *,
        alert,
        timestamp: datetime,
        metrics: list[dict] | None,
        title: str,
        message: str,
        news_id: int,
    ):
        return self.repository.create(
            title=title,
            message=message,
            user_id=alert.user_id,
            alert_id=alert.id,
            news_id=news_id,
            timestamp=timestamp,
            metrics=_normalize_metrics(metrics),
        )

    def list_for_alert(self, alert):
        return self.repository.list_for_alert(alert.id)

    def get_for_alert(self, alert, notification_id: int):
        notification = self.repository.get_by_id_for_alert(notification_id, alert.id)
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found for this alert.",
            )
        return notification

    def update_for_alert(self, alert, notification_id: int, payload):
        notification = self.get_for_alert(alert, notification_id)
        fields: dict = {}
        if getattr(payload, "timestamp", None) is not None:
            fields["timestamp"] = payload.timestamp
        if getattr(payload, "metrics", None) is not None:
            fields["metrics"] = _normalize_metrics(payload.metrics)
        return self.repository.update(notification, **fields) if fields else notification

    def delete_for_alert(self, alert, notification_id: int) -> None:
        notification = self.get_for_alert(alert, notification_id)
        self.repository.delete(notification)

    # ── Endpoints "me" (UI) ──────────────────────────────────────────

    def list_for_user(self, user_id: int):
        return self.repository.list_for_user(user_id)

    def get_for_user(self, notification_id: int, user_id: int):
        notification = self.repository.get_by_id_for_user(notification_id, user_id)
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found.",
            )
        return notification

    def mark_as_read(self, notification_id: int, user_id: int):
        notification = self.get_for_user(notification_id, user_id)
        return self.repository.update_read_status(notification, True)

    def mark_as_unread(self, notification_id: int, user_id: int):
        notification = self.get_for_user(notification_id, user_id)
        return self.repository.update_read_status(notification, False)

    def delete_for_user(self, notification_id: int, user_id: int) -> None:
        notification = self.get_for_user(notification_id, user_id)
        self.repository.delete(notification)


# Helper utilizado por matching.py
def build_default_metrics(news, source_name: str | None) -> list[dict]:
    """Métricas mínimas adjuntas a una notificación generada por matching."""
    metrics: list[dict] = []
    summary = (getattr(news, "summary", None) or "").strip()
    title = (getattr(news, "title", None) or "").strip()
    metrics.append({"name": "summary_length_chars", "value": float(len(summary))})
    metrics.append({"name": "title_length_chars", "value": float(len(title))})
    if source_name:
        # Una métrica simple: 1.0 si la news viene de una fuente conocida.
        metrics.append({"name": "has_known_source", "value": 1.0})
    else:
        metrics.append({"name": "has_known_source", "value": 0.0})
    return metrics
