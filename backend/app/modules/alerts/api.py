"""API del módulo alerts: se definirán los endpoints REST para crear, consultar y gestionar alertas."""

from fastapi import APIRouter, Depends

from backend.app.api.deps import get_current_user


router = APIRouter(
    prefix="/alerts",
    tags=["alerts"],
    dependencies=[Depends(get_current_user)],
)