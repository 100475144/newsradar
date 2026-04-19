"""Sources API for Sprint 2 CRUD.

Permisos:
- Lector: solo lectura (GET).
- Gestor / Admin: lectura y escritura (CRUD completo).
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_verified_user, get_db, require_role
from app.modules.auth.models import User
from app.modules.auth.schemas import UserRole
from app.modules.sources.models import Source
from app.modules.sources.repository import SourceRepository
from app.modules.sources.schemas import SourceCreate, SourceResponse, SourceUpdate
from app.modules.sources.service import SourceService


router = APIRouter(prefix="/sources", tags=["sources"])

_gestor_or_admin = require_role(UserRole.ADMIN, UserRole.GESTOR)


def get_source_service(db: Session = Depends(get_db)) -> SourceService:
    return SourceService(SourceRepository(db))


# ── Read endpoints (any authenticated user) ──────────────────────────

@router.get("", response_model=List[SourceResponse], status_code=status.HTTP_200_OK)
def list_sources(
    current_user: User = Depends(get_current_active_verified_user),
    source_service: SourceService = Depends(get_source_service),
) -> List[Source]:
    return source_service.list_sources(current_user.id)


@router.get("/{source_id}", response_model=SourceResponse, status_code=status.HTTP_200_OK)
def read_source(
    source_id: int = Path(..., ge=1),
    current_user: User = Depends(get_current_active_verified_user),
    source_service: SourceService = Depends(get_source_service),
) -> Source:
    try:
        return source_service.get_source(source_id, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# ── Write endpoints (gestor + admin only) ────────────────────────────

@router.post("", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
def create_source(
    source_data: SourceCreate,
    current_user: User = Depends(_gestor_or_admin),
    source_service: SourceService = Depends(get_source_service),
) -> Source:
    try:
        return source_service.create_source(source_data, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.put("/{source_id}", response_model=SourceResponse, status_code=status.HTTP_200_OK)
def update_source(
    source_data: SourceUpdate,
    source_id: int = Path(..., ge=1),
    current_user: User = Depends(_gestor_or_admin),
    source_service: SourceService = Depends(get_source_service),
) -> Source:
    try:
        return source_service.update_source(source_id, current_user.id, source_data)
    except ValueError as exc:
        message = str(exc)
        status_code = status.HTTP_404_NOT_FOUND if message == "Source not found." else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=message) from exc


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_source(
    source_id: int = Path(..., ge=1),
    current_user: User = Depends(_gestor_or_admin),
    source_service: SourceService = Depends(get_source_service),
) -> None:
    try:
        source_service.delete_source(source_id, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/{source_id}/activate", response_model=SourceResponse, status_code=status.HTTP_200_OK)
def activate_source(
    source_id: int = Path(..., ge=1),
    current_user: User = Depends(_gestor_or_admin),
    source_service: SourceService = Depends(get_source_service),
) -> Source:
    try:
        return source_service.activate_source(source_id, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/{source_id}/deactivate", response_model=SourceResponse, status_code=status.HTTP_200_OK)
def deactivate_source(
    source_id: int = Path(..., ge=1),
    current_user: User = Depends(_gestor_or_admin),
    source_service: SourceService = Depends(get_source_service),
) -> Source:
    try:
        return source_service.deactivate_source(source_id, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
