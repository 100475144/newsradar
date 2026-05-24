"""Endpoints CRUD de la entidad Role.

Alineados con la API oficial (`main.py` de aula global):
- GET    /api/v1/roles
- POST   /api/v1/roles
- GET    /api/v1/roles/{role_id}
- PUT    /api/v1/roles/{role_id}
- DELETE /api/v1/roles/{role_id}

Permisos:
- Lectura: cualquier usuario autenticado.
- Escritura: cualquier usuario autenticado (matchea la API oficial). En la
  práctica, los gestores no necesitan crear/borrar roles porque CAMBIO #1bis
  asigna "gestor" automáticamente, pero los endpoints existen para
  cumplimiento estricto del contrato.
"""

import re

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_verified_user, get_db
from app.core.db_utils import safe_commit
from app.modules.auth.models import Role, User
from app.modules.auth.schemas import RoleCreate, RoleResponse, RoleUpdate

router = APIRouter(prefix="/roles", tags=["roles"])


def _get_role_or_404(db: Session, role_id: int) -> Role:
    role = db.query(Role).filter(Role.id == role_id).first()
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found.",
        )
    return role


@router.get("", response_model=list[RoleResponse])
def list_roles(
    _: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
) -> list[Role]:
    return db.query(Role).order_by(Role.id).all()


@router.post(
    "",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_role(
    payload: RoleCreate,
    _: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
) -> Role:
    name = payload.name.strip()
    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role name cannot be empty or whitespace.",
        )
    if len(name) > 90:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role name must not exceed 90 characters.",
        )
    if not re.match(r'^[\w \t-]+$', name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role name contains invalid characters. Only alphanumeric characters, spaces, hyphens and underscores are allowed.",
        )
    existing = db.query(Role).filter(sa_func.lower(Role.name) == name.lower()).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A role with this name already exists.",
        )
    role = Role(name=name)
    db.add(role)
    safe_commit(db, conflict_detail="A role with this name already exists.")
    db.refresh(role)
    return role


@router.get("/{role_id}", response_model=RoleResponse)
def get_role(
    role_id: int,
    _: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
) -> Role:
    return _get_role_or_404(db, role_id)


@router.put("/{role_id}", response_model=RoleResponse)
def update_role(
    role_id: int,
    payload: RoleUpdate,
    _: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
) -> Role:
    role = _get_role_or_404(db, role_id)
    if payload.name is not None:
        new_name = payload.name.strip()
        clash = (
            db.query(Role)
            .filter(sa_func.lower(Role.name) == new_name.lower(), Role.id != role_id)
            .first()
        )
        if clash is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A role with this name already exists.",
            )
        role.name = new_name
    db.add(role)
    safe_commit(db, conflict_detail="A role with this name already exists.")
    db.refresh(role)
    return role


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_role(
    role_id: int,
    _: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
) -> Response:
    role = _get_role_or_404(db, role_id)
    if role.users:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete a role that is currently assigned to users.",
        )
    db.delete(role)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
