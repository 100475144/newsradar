"""Servicio del módulo notifications: se implementará la lógica de generación y gestión de notificaciones."""

from fastapi import HTTPException, status

from app.modules.notifications.repository import NotificationRepository
from app.modules.notifications.schemas import NotificationCreate, NotificationUpdate


class NotificationService:
    def __init__(self, repository: NotificationRepository):
        self.repository = repository

    def create_notification(self, data: NotificationCreate, user_id: int):
        return self.repository.create(
            title=data.title.strip(),
            message=data.message.strip(),
            created_by=user_id,
        )

    def list_notifications(self, user_id: int):
        return self.repository.list_for_user(user_id)

    def get_notification(self, notification_id: int, user_id: int):
        notification = self.repository.get_by_id_for_user(notification_id, user_id)
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found.",
            )
        return notification

    def update_notification(self, notification_id: int, data: NotificationUpdate, user_id: int):
        notification = self.get_notification(notification_id, user_id)
        if data.is_read is None:
            return notification
        return self.repository.update_read_status(notification, data.is_read)

    def mark_as_read(self, notification_id: int, user_id: int):
        notification = self.get_notification(notification_id, user_id)
        return self.repository.update_read_status(notification, True)

    def mark_as_unread(self, notification_id: int, user_id: int):
        notification = self.get_notification(notification_id, user_id)
        return self.repository.update_read_status(notification, False)

    def delete_notification(self, notification_id: int, user_id: int):
        notification = self.get_notification(notification_id, user_id)
        self.repository.delete(notification)
        return {"message": "Notification deleted successfully."}
        