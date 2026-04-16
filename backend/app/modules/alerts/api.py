"""API del módulo alerts: se definirán los endpoints REST para crear, consultar y gestionar alertas."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.modules.alerts.recommender import suggest_expanded_keywords
from app.modules.alerts.repository import AlertRepository
from app.modules.alerts.schemas import AlertCreate, AlertResponse, AlertUpdate
from app.modules.alerts.service import AlertService
from app.modules.sources.repository import SourceRepository


router = APIRouter(prefix="/alerts", tags=["alerts"])


def get_alert_service(db: Session = Depends(get_db)) -> AlertService:
    return AlertService(AlertRepository(db), SourceRepository(db))


@router.get("/", response_model=list[AlertResponse])
def list_alerts(
    current_user=Depends(get_current_user),
    service: AlertService = Depends(get_alert_service),
):
    return service.list_alerts(current_user.id)


@router.post("/", response_model=AlertResponse)
def create_alert(
    payload: AlertCreate,
    current_user=Depends(get_current_user),
    service: AlertService = Depends(get_alert_service),
):
    return service.create_alert(payload, current_user.id)


@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert(
    alert_id: int,
    current_user=Depends(get_current_user),
    service: AlertService = Depends(get_alert_service),
):
    return service.get_alert(alert_id, current_user.id)


@router.put("/{alert_id}", response_model=AlertResponse)
def update_alert(
    alert_id: int,
    payload: AlertUpdate,
    current_user=Depends(get_current_user),
    service: AlertService = Depends(get_alert_service),
):
    return service.update_alert(alert_id, payload, current_user.id)


@router.delete("/{alert_id}")
def delete_alert(
    alert_id: int,
    current_user=Depends(get_current_user),
    service: AlertService = Depends(get_alert_service),
):
    return service.delete_alert(alert_id, current_user.id)


@router.patch("/{alert_id}/activate", response_model=AlertResponse)
def activate_alert(
    alert_id: int,
    current_user=Depends(get_current_user),
    service: AlertService = Depends(get_alert_service),
):
    return service.activate_alert(alert_id, current_user.id)


@router.patch("/{alert_id}/deactivate", response_model=AlertResponse)
def deactivate_alert(
    alert_id: int,
    current_user=Depends(get_current_user),
    service: AlertService = Depends(get_alert_service),
):
    return service.deactivate_alert(alert_id, current_user.id)


@router.get("/suggestions/{keyword}")
def get_keyword_suggestions(keyword: str):
    suggestions = suggest_expanded_keywords(keyword)
    return {
        "keyword": keyword,
        "suggestions": suggestions,
        "count": len(suggestions),
    }
    