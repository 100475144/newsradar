"""APIs de notifications.

Endpoints alineados con la API oficial (T6.5):
- GET    /api/v1/users/{user_id}/alerts/{alert_id}/notifications
- POST   /api/v1/users/{user_id}/alerts/{alert_id}/notifications
- GET    /api/v1/users/{user_id}/alerts/{alert_id}/notifications/{notification_id}
- PUT    /api/v1/users/{user_id}/alerts/{alert_id}/notifications/{notification_id}
- DELETE /api/v1/users/{user_id}/alerts/{alert_id}/notifications/{notification_id}

Endpoints añadidos para la UI:
- GET    /api/v1/users/me/notifications              — bandeja de entrada
- GET    /api/v1/users/me/notifications/{id}/details — schema enriquecido
- PATCH  /api/v1/users/me/notifications/{id}/read
- PATCH  /api/v1/users/me/notifications/{id}/unread
- DELETE /api/v1/users/me/notifications/{id}
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_verified_user, get_db
from app.modules.alerts.repository import AlertRepository
from app.modules.alerts.service import AlertService
from app.modules.auth.models import User
from app.modules.auth.schemas import UserRole
from app.modules.notifications.repository import NotificationRepository
from app.modules.notifications.schemas import (
    NotificationCreate,
    NotificationDetailResponse,
    NotificationResponse,
    NotificationUpdate,
)
from app.modules.notifications.service import NotificationService


def get_notification_service(db: Session = Depends(get_db)) -> NotificationService:
    return NotificationService(NotificationRepository(db))


def get_alert_service(db: Session = Depends(get_db)) -> AlertService:
    return AlertService(AlertRepository(db))


def _ensure_user_access(current_user: User, target_user_id: int) -> None:
    if current_user.role == UserRole.ADMIN.value:
        return
    if current_user.id != target_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own notifications.",
        )


# ─────────────────────────────────────────────────────────────────────
# Endpoints anidados oficiales: /users/{u}/alerts/{a}/notifications
# ─────────────────────────────────────────────────────────────────────


router = APIRouter(prefix="/users", tags=["notifications"])


def _get_owned_alert(
    user_id: int,
    alert_id: int,
    current_user: User,
    alert_service: AlertService,
):
    _ensure_user_access(current_user, user_id)
    return alert_service.get_alert(alert_id, user_id)


@router.get(
    "/{user_id}/alerts/{alert_id}/notifications",
    response_model=list[NotificationResponse],
)
def list_alert_notifications(
    user_id: int = Path(..., ge=1),
    alert_id: int = Path(..., ge=1),
    current_user: User = Depends(get_current_active_verified_user),
    alert_service: AlertService = Depends(get_alert_service),
    notification_service: NotificationService = Depends(get_notification_service),
):
    alert = _get_owned_alert(user_id, alert_id, current_user, alert_service)
    return notification_service.list_for_alert(alert)


@router.post(
    "/{user_id}/alerts/{alert_id}/notifications",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_alert_notification(
    payload: NotificationCreate,
    user_id: int = Path(..., ge=1),
    alert_id: int = Path(..., ge=1),
    current_user: User = Depends(get_current_active_verified_user),
    alert_service: AlertService = Depends(get_alert_service),
    notification_service: NotificationService = Depends(get_notification_service),
):
    # Verificar acceso/ownership de la alerta antes de denegar.
    _get_owned_alert(user_id, alert_id, current_user, alert_service)
    # Crear notificación canónica desligada de news: como nuestra UI necesita
    # title/message obligatorios, autogeneramos placeholders cuando se crea
    # vía endpoint canónico. ``news_id`` se requiere por unicidad lógica;
    # usamos 0 cuando no hay news asociada — se considera placeholder.
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=(
            "Notifications are generated automatically by the matching engine. "
            "POST is exposed for contract compliance only."
        ),
    )


@router.get(
    "/{user_id}/alerts/{alert_id}/notifications/{notification_id}",
    response_model=NotificationResponse,
)
def get_alert_notification(
    user_id: int = Path(..., ge=1),
    alert_id: int = Path(..., ge=1),
    notification_id: int = Path(..., ge=1),
    current_user: User = Depends(get_current_active_verified_user),
    alert_service: AlertService = Depends(get_alert_service),
    notification_service: NotificationService = Depends(get_notification_service),
):
    alert = _get_owned_alert(user_id, alert_id, current_user, alert_service)
    return notification_service.get_for_alert(alert, notification_id)


@router.put(
    "/{user_id}/alerts/{alert_id}/notifications/{notification_id}",
    response_model=NotificationResponse,
)
def update_alert_notification(
    payload: NotificationUpdate,
    user_id: int = Path(..., ge=1),
    alert_id: int = Path(..., ge=1),
    notification_id: int = Path(..., ge=1),
    current_user: User = Depends(get_current_active_verified_user),
    alert_service: AlertService = Depends(get_alert_service),
    notification_service: NotificationService = Depends(get_notification_service),
):
    alert = _get_owned_alert(user_id, alert_id, current_user, alert_service)
    return notification_service.update_for_alert(alert, notification_id, payload)


@router.delete(
    "/{user_id}/alerts/{alert_id}/notifications/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_alert_notification(
    user_id: int = Path(..., ge=1),
    alert_id: int = Path(..., ge=1),
    notification_id: int = Path(..., ge=1),
    current_user: User = Depends(get_current_active_verified_user),
    alert_service: AlertService = Depends(get_alert_service),
    notification_service: NotificationService = Depends(get_notification_service),
):
    alert = _get_owned_alert(user_id, alert_id, current_user, alert_service)
    notification_service.delete_for_alert(alert, notification_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ─────────────────────────────────────────────────────────────────────
# Endpoints "me": bandeja de entrada del usuario logueado (añadidos)
# ─────────────────────────────────────────────────────────────────────


me_router = APIRouter(prefix="/users/me/notifications", tags=["notifications"])


@me_router.get("", response_model=list[NotificationDetailResponse])
def list_my_notifications(
    current_user: User = Depends(get_current_active_verified_user),
    service: NotificationService = Depends(get_notification_service),
):
    return service.list_for_user(current_user.id)


@me_router.get("/{notification_id}/details", response_model=NotificationDetailResponse)
def get_my_notification_details(
    notification_id: int = Path(..., ge=1),
    current_user: User = Depends(get_current_active_verified_user),
    service: NotificationService = Depends(get_notification_service),
):
    return service.get_for_user(notification_id, current_user.id)


@me_router.patch("/{notification_id}/read", response_model=NotificationDetailResponse)
def mark_my_notification_read(
    notification_id: int = Path(..., ge=1),
    current_user: User = Depends(get_current_active_verified_user),
    service: NotificationService = Depends(get_notification_service),
):
    return service.mark_as_read(notification_id, current_user.id)


@me_router.patch("/{notification_id}/unread", response_model=NotificationDetailResponse)
def mark_my_notification_unread(
    notification_id: int = Path(..., ge=1),
    current_user: User = Depends(get_current_active_verified_user),
    service: NotificationService = Depends(get_notification_service),
):
    return service.mark_as_unread(notification_id, current_user.id)


@me_router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_my_notification(
    notification_id: int = Path(..., ge=1),
    current_user: User = Depends(get_current_active_verified_user),
    service: NotificationService = Depends(get_notification_service),
):
    service.delete_for_user(notification_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
