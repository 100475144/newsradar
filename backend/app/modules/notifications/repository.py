"""Repositorio del módulo notifications: irá el acceso a datos de notificaciones (listado, creación, marcado de lectura, etc.)."""

from sqlalchemy.orm import Session

from app.modules.notifications.models import Notification


class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, *, title: str, message: str, created_by: int) -> Notification:
        notification = Notification(
            title=title,
            message=message,
            created_by=created_by,
            is_read=False,
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def list_for_user(self, user_id: int) -> list[Notification]:
        return (
            self.db.query(Notification)
            .filter(Notification.created_by == user_id)
            .order_by(Notification.id.desc())
            .all()
        )

    def get_by_id_for_user(self, notification_id: int, user_id: int) -> Notification | None:
        return (
            self.db.query(Notification)
            .filter(
                Notification.id == notification_id,
                Notification.created_by == user_id,
            )
            .first()
        )

    def update_read_status(self, notification: Notification, is_read: bool) -> Notification:
        notification.is_read = is_read
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def delete(self, notification: Notification) -> None:
        self.db.delete(notification)
        self.db.commit()
        