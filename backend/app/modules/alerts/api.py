"""API del módulo alerts: endpoints REST para crear, consultar y gestionar alertas.

Permisos:
- Lector: solo lectura (GET).
- Gestor / Admin: lectura y escritura (CRUD completo).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_verified_user, get_db, require_role
from app.core.iptc import IPTC_CATEGORIES
from app.modules.alerts.recommender import suggest_expanded_keywords
from app.modules.alerts.repository import AlertRepository
from app.modules.alerts.schemas import AlertCreate, AlertResponse, AlertUpdate
from app.modules.alerts.service import AlertService
from app.modules.auth.models import User
from app.modules.auth.schemas import UserRole
from app.modules.sources.repository import SourceRepository


router = APIRouter(prefix="/alerts", tags=["alerts"])

# Dependency shortcuts
_gestor_or_admin = require_role(UserRole.ADMIN, UserRole.GESTOR)


def get_alert_service(db: Session = Depends(get_db)) -> AlertService:
    return AlertService(AlertRepository(db), SourceRepository(db))


# ── Read endpoints (any authenticated user) ──────────────────────────

@router.get("/", response_model=list[AlertResponse])
def list_alerts(
    current_user: User = Depends(get_current_active_verified_user),
    service: AlertService = Depends(get_alert_service),
):
    return service.list_alerts(current_user.id)


@router.get("/categories")
def list_iptc_categories():
    """Return all valid IPTC Media Topics first-level categories."""
    return [
        {"code": code, "label": label}
        for code, label in IPTC_CATEGORIES.items()
    ]


@router.get("/suggestions/{keyword}")
def get_keyword_suggestions(keyword: str):
    suggestions = suggest_expanded_keywords(keyword)
    return {
        "keyword": keyword,
        "suggestions": suggestions,
        "count": len(suggestions),
    }


@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert(
    alert_id: int,
    current_user: User = Depends(get_current_active_verified_user),
    service: AlertService = Depends(get_alert_service),
):
    return service.get_alert(alert_id, current_user.id)


# ── Write endpoints (gestor + admin only) ────────────────────────────

@router.post("/", response_model=AlertResponse)
def create_alert(
    payload: AlertCreate,
    current_user: User = Depends(_gestor_or_admin),
    service: AlertService = Depends(get_alert_service),
):
    return service.create_alert(payload, current_user.id)


@router.put("/{alert_id}", response_model=AlertResponse)
def update_alert(
    alert_id: int,
    payload: AlertUpdate,
    current_user: User = Depends(_gestor_or_admin),
    service: AlertService = Depends(get_alert_service),
):
    return service.update_alert(alert_id, payload, current_user.id)


@router.delete("/{alert_id}")
def delete_alert(
    alert_id: int,
    current_user: User = Depends(_gestor_or_admin),
    service: AlertService = Depends(get_alert_service),
):
    return service.delete_alert(alert_id, current_user.id)


@router.patch("/{alert_id}/activate", response_model=AlertResponse)
def activate_alert(
    alert_id: int,
    current_user: User = Depends(_gestor_or_admin),
    service: AlertService = Depends(get_alert_service),
):
    return service.activate_alert(alert_id, current_user.id)


@router.patch("/{alert_id}/deactivate", response_model=AlertResponse)
def deactivate_alert(
    alert_id: int,
    current_user: User = Depends(_gestor_or_admin),
    service: AlertService = Depends(get_alert_service),
):
    return service.deactivate_alert(alert_id, current_user.id)
