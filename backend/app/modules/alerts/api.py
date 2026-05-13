"""API del módulo alerts.

Endpoints alineados con la API oficial (T6.4):
- GET    /api/v1/users/{user_id}/alerts
- POST   /api/v1/users/{user_id}/alerts
- GET    /api/v1/users/{user_id}/alerts/{alert_id}
- PUT    /api/v1/users/{user_id}/alerts/{alert_id}
- DELETE /api/v1/users/{user_id}/alerts/{alert_id}

Endpoints añadidos sobre el contrato oficial (permitido por el profesor):
- GET    /api/v1/alerts/categories             — lista IPTC (frontend usa)
- GET    /api/v1/alerts/suggestions/{keyword}  — recommender 3-10 términos
- GET    /api/v1/alerts/me/stats               — stats del usuario logueado
- PATCH  /api/v1/users/{user_id}/alerts/{id}/activate
- PATCH  /api/v1/users/{user_id}/alerts/{id}/deactivate
- GET    /api/v1/users/me/alerts (alias práctico para no exigir user_id en URL)

Permisos: cada usuario solo accede a sus propias alertas (CAMBIO #2 oficial:
las alertas y notificaciones son per-usuario). El path ``user_id`` debe coincidir
con el usuario autenticado, salvo que sea ``admin`` (que puede ver todo).
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_verified_user, get_db, require_role
from app.core.iptc import IPTC_CATEGORIES
from app.modules.alerts.recommender import suggest_expanded_keywords
from app.modules.alerts.repository import AlertRepository
from app.modules.alerts.schemas import AlertCreateInternal, AlertResponse, AlertUpdate
from app.modules.alerts.service import AlertService
from app.modules.auth.models import User
from app.modules.auth.schemas import UserRole


# ── Rutas auxiliares (no anidadas) ───────────────────────────────────


helpers_router = APIRouter(prefix="/alerts", tags=["alerts"])


def get_alert_service(db: Session = Depends(get_db)) -> AlertService:
    return AlertService(AlertRepository(db))


@helpers_router.get("/categories")
def list_iptc_categories(
    _: User = Depends(get_current_active_verified_user),
):
    return [{"code": code, "label": label} for code, label in IPTC_CATEGORIES.items()]


@helpers_router.get("/suggestions/{keyword}")
def get_keyword_suggestions(
    keyword: str,
    _: User = Depends(get_current_active_verified_user),
):
    suggestions = suggest_expanded_keywords(keyword)
    return {
        "keyword": keyword,
        "suggestions": suggestions,
        "count": len(suggestions),
    }


@helpers_router.get("/me/stats")
def my_alerts_stats(
    current_user: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    """Stats por categoría de las alertas del usuario logueado (CAMBIO #2)."""
    service = AlertService(AlertRepository(db))
    user_alerts = service.list_alerts_for_user(current_user.id)
    counts: dict[str, int] = {}
    for alert in user_alerts:
        for cat in alert.categories or []:
            code = (cat.get("code") or "uncategorized") if isinstance(cat, dict) else "uncategorized"
            counts[code] = counts.get(code, 0) + 1
    return {
        "total_alerts": len(user_alerts),
        "by_category": [
            {"category": code, "count": count}
            for code, count in sorted(counts.items(), key=lambda kv: -kv[1])
        ],
    }


# ── Rutas anidadas oficiales: /users/{user_id}/alerts ────────────────


router = APIRouter(prefix="/users", tags=["alerts"])

_gestor_or_admin = require_role(UserRole.ADMIN, UserRole.GESTOR)


def _ensure_user_access(current_user: User, target_user_id: int) -> None:
    """El usuario solo puede operar sobre sus propias alertas (salvo admin)."""
    if current_user.role == UserRole.ADMIN.value:
        return
    if current_user.id != target_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own alerts.",
        )


@router.get("/{user_id}/alerts", response_model=list[AlertResponse])
def list_user_alerts(
    user_id: int = Path(..., ge=1),
    current_user: User = Depends(get_current_active_verified_user),
    service: AlertService = Depends(get_alert_service),
):
    _ensure_user_access(current_user, user_id)
    return service.list_alerts_for_user(user_id)


@router.post(
    "/{user_id}/alerts",
    response_model=AlertResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user_alert(
    payload: AlertCreateInternal,
    user_id: int = Path(..., ge=1),
    current_user: User = Depends(_gestor_or_admin),
    service: AlertService = Depends(get_alert_service),
    db: Session = Depends(get_db),
):
    _ensure_user_access(current_user, user_id)
    target_user = db.query(User).filter(User.id == user_id).first()
    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return service.create_alert(payload, user_id)


@router.get("/{user_id}/alerts/{alert_id}", response_model=AlertResponse)
def get_user_alert(
    user_id: int = Path(..., ge=1),
    alert_id: int = Path(..., ge=1),
    current_user: User = Depends(get_current_active_verified_user),
    service: AlertService = Depends(get_alert_service),
):
    _ensure_user_access(current_user, user_id)
    return service.get_alert(alert_id, user_id)


@router.put("/{user_id}/alerts/{alert_id}", response_model=AlertResponse)
def update_user_alert(
    payload: AlertUpdate,
    user_id: int = Path(..., ge=1),
    alert_id: int = Path(..., ge=1),
    current_user: User = Depends(_gestor_or_admin),
    service: AlertService = Depends(get_alert_service),
):
    _ensure_user_access(current_user, user_id)
    return service.update_alert(alert_id, payload, user_id)


@router.delete(
    "/{user_id}/alerts/{alert_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_user_alert(
    user_id: int = Path(..., ge=1),
    alert_id: int = Path(..., ge=1),
    current_user: User = Depends(_gestor_or_admin),
    service: AlertService = Depends(get_alert_service),
):
    _ensure_user_access(current_user, user_id)
    service.delete_alert(alert_id, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/{user_id}/alerts/{alert_id}/activate",
    response_model=AlertResponse,
)
def activate_user_alert(
    user_id: int = Path(..., ge=1),
    alert_id: int = Path(..., ge=1),
    current_user: User = Depends(_gestor_or_admin),
    service: AlertService = Depends(get_alert_service),
):
    _ensure_user_access(current_user, user_id)
    return service.activate_alert(alert_id, user_id)


@router.patch(
    "/{user_id}/alerts/{alert_id}/deactivate",
    response_model=AlertResponse,
)
def deactivate_user_alert(
    user_id: int = Path(..., ge=1),
    alert_id: int = Path(..., ge=1),
    current_user: User = Depends(_gestor_or_admin),
    service: AlertService = Depends(get_alert_service),
):
    _ensure_user_access(current_user, user_id)
    return service.deactivate_alert(alert_id, user_id)


# ── Atajo "me": evita exigir el user_id explícito al frontend ────────


me_router = APIRouter(prefix="/users/me", tags=["alerts"])


@me_router.get("/alerts", response_model=list[AlertResponse])
def list_my_alerts(
    current_user: User = Depends(get_current_active_verified_user),
    service: AlertService = Depends(get_alert_service),
):
    return service.list_alerts_for_user(current_user.id)


@me_router.post(
    "/alerts",
    response_model=AlertResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_my_alert(
    payload: AlertCreateInternal,
    current_user: User = Depends(_gestor_or_admin),
    service: AlertService = Depends(get_alert_service),
):
    return service.create_alert(payload, current_user.id)
