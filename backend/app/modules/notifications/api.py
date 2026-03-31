"""API del módulo notifications: se definirán los endpoints REST para consultar y gestionar notificaciones."""

from fastapi import APIRouter, Depends

from backend.app.api.deps import get_current_user


router = APIRouter(
    prefix="/notifications",
    tags=["notifications"],
    dependencies=[Depends(get_current_user)],
)
