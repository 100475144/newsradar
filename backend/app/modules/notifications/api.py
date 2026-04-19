"""API del módulo notifications: se definirán los endpoints REST para consultar y gestionar notificaciones."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_verified_user, get_db
from app.modules.notifications.repository import NotificationRepository
from app.modules.notifications.schemas import NotificationCreate, NotificationResponse, NotificationUpdate
from app.modules.notifications.service import NotificationService


router = APIRouter(prefix="/notifications", tags=["notifications"])


def get_notification_service(db: Session = Depends(get_db)) -> NotificationService:
    return NotificationService(NotificationRepository(db))


@router.get("/", response_model=list[NotificationResponse])
def list_notifications(
    current_user=Depends(get_current_active_verified_user),
    service: NotificationService = Depends(get_notification_service),
):
    return service.list_notifications(current_user.id)


@router.post("/", response_model=NotificationResponse)
def create_notification(
    payload: NotificationCreate,
    current_user=Depends(get_current_active_verified_user),
    service: NotificationService = Depends(get_notification_service),
):
    return service.create_notification(payload, current_user.id)


@router.get("/{notification_id}", response_model=NotificationResponse)
def get_notification(
    notification_id: int,
    current_user=Depends(get_current_active_verified_user),
    service: NotificationService = Depends(get_notification_service),
):
    return service.get_notification(notification_id, current_user.id)


@router.put("/{notification_id}", response_model=NotificationResponse)
def update_notification(
    notification_id: int,
    payload: NotificationUpdate,
    current_user=Depends(get_current_active_verified_user),
    service: NotificationService = Depends(get_notification_service),
):
    return service.update_notification(notification_id, payload, current_user.id)


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_as_read(
    notification_id: int,
    current_user=Depends(get_current_active_verified_user),
    service: NotificationService = Depends(get_notification_service),
):
    return service.mark_as_read(notification_id, current_user.id)


@router.patch("/{notification_id}/unread", response_model=NotificationResponse)
def mark_notification_as_unread(
    notification_id: int,
    current_user=Depends(get_current_active_verified_user),
    service: NotificationService = Depends(get_notification_service),
):
    return service.mark_as_unread(notification_id, current_user.id)


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    current_user=Depends(get_current_active_verified_user),
    service: NotificationService = Depends(get_notification_service),
):
    return service.delete_notification(notification_id, current_user.id)
    
