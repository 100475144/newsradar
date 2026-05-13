"""Repositorio de notifications adaptado al schema oficial (T6.5)."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.modules.notifications.models import Notification


class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        *,
        title: str,
        message: str,
        user_id: int,
        alert_id: int,
        news_id: int | None = None,
        timestamp: datetime | None = None,
        metrics: list[dict] | None = None,
    ) -> Notification:
        if news_id is not None:
            existing = self.get_by_delivery_key(
                user_id=user_id, alert_id=alert_id, news_id=news_id
            )
            if existing:
                return existing

        notification = Notification(
            title=title,
            message=message,
            user_id=user_id,
            alert_id=alert_id,
            news_id=news_id,
            is_read=False,
            timestamp=timestamp or datetime.now(timezone.utc),
            metrics=metrics or [],
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def get_by_delivery_key(
        self, *, user_id: int, alert_id: int, news_id: int
    ) -> Notification | None:
        return (
            self.db.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.alert_id == alert_id,
                Notification.news_id == news_id,
            )
            .first()
        )

    def list_for_user(self, user_id: int) -> list[Notification]:
        return (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id)
            .order_by(Notification.id.desc())
            .all()
        )

    def list_for_alert(self, alert_id: int) -> list[Notification]:
        return (
            self.db.query(Notification)
            .filter(Notification.alert_id == alert_id)
            .order_by(Notification.id.desc())
            .all()
        )

    def get_by_id(self, notification_id: int) -> Notification | None:
        return (
            self.db.query(Notification)
            .filter(Notification.id == notification_id)
            .first()
        )

    def get_by_id_for_user(
        self, notification_id: int, user_id: int
    ) -> Notification | None:
        return (
            self.db.query(Notification)
            .filter(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
            .first()
        )

    def get_by_id_for_alert(
        self, notification_id: int, alert_id: int
    ) -> Notification | None:
        return (
            self.db.query(Notification)
            .filter(
                Notification.id == notification_id,
                Notification.alert_id == alert_id,
            )
            .first()
        )

    def update(self, notification: Notification, **fields) -> Notification:
        for key, value in fields.items():
            if value is not None:
                setattr(notification, key, value)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def update_read_status(
        self, notification: Notification, is_read: bool
    ) -> Notification:
        notification.is_read = is_read
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def delete(self, notification: Notification) -> None:
        self.db.delete(notification)
        self.db.commit()
