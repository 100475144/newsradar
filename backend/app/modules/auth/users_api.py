"""Endpoints CRUD oficiales de Users.

Alineados con el ``main.py`` del aula global:
- GET    /api/v1/users
- POST   /api/v1/users           (status 201)
- GET    /api/v1/users/{user_id}
- PUT    /api/v1/users/{user_id}
- DELETE /api/v1/users/{user_id} (status 204)

Estos endpoints conviven con los anidados ``/users/{user_id}/alerts`` y
``/users/me/alerts`` registrados por otros módulos. FastAPI resuelve por
ruta exacta sin ambigüedad.

Permisos:
- POST y operaciones sobre OTROS usuarios: solo admin.
- GET ``/users`` (list): cualquier usuario autenticado (la API oficial no
  exige admin para listar).
- GET/PUT sobre el propio usuario: cualquier autenticado.
- DELETE: admin o el propio usuario.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_verified_user, get_db, require_role
from app.core.db_utils import safe_commit
from app.core.security import get_password_hash
from app.modules.auth.models import Role, User
from app.modules.auth.schemas import (
    UserCreate,
    UserResponse,
    UserRole,
    UserUpdate,
)


router = APIRouter(prefix="/users", tags=["users"])

_admin_only = require_role(UserRole.ADMIN)


def _get_user_or_404(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return user


def _ensure_self_or_admin(current_user: User, target_user_id: int) -> None:
    if current_user.role == UserRole.ADMIN.value:
        return
    if current_user.id != target_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only modify your own user data.",
        )


def _set_role_ids(db: Session, user: User, role_ids: list[int]) -> None:
    """Reemplaza los roles del usuario por los nuevos role_ids."""
    if not role_ids:
        user.roles = []
        return
    roles = db.query(Role).filter(Role.id.in_(role_ids)).all()
    found_ids = {r.id for r in roles}
    missing = [rid for rid in role_ids if rid not in found_ids]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Roles not found: {missing}",
        )
    user.roles = roles


# ─────────────────────────────────────────────────────────────────────


@router.get("", response_model=List[UserResponse])
def list_users(
    _: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    return db.query(User).order_by(User.id).all()


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    payload: UserCreate,
    _: User = Depends(_admin_only),
    db: Session = Depends(get_db),
):
    existing = db.query(User).filter(User.email == payload.email.strip().lower()).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    # Resolve role_ids: default to gestor if not provided or empty.
    gestor = db.query(Role).filter(Role.name == "gestor").first()
    role_ids = payload.role_ids

    if role_ids is not None and len(role_ids) > 0:
        # Validate: only 1 role allowed.
        if len(role_ids) > 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Users can only have one role.",
            )
        target_role_id = role_ids[0]
        role = db.query(Role).filter(Role.id == target_role_id).first()
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role with id {target_role_id} does not exist.",
            )
        assigned_roles = [role]
    else:
        # Default to gestor role.
        assigned_roles = [gestor] if gestor else []

    # Determine the role name for the legacy 'role' column.
    role_name = assigned_roles[0].name if assigned_roles else "gestor"

    user = User(
        email=payload.email.strip().lower(),
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        organization=payload.organization.strip(),
        phone=payload.phone.strip(),
        hashed_password=get_password_hash(payload.password),
        role=role_name,
        is_active=True,
        is_verified=True,  # admin-created users no need email verification
    )
    user.roles = assigned_roles
    db.add(user)
    safe_commit(db, conflict_detail="A user with this email already exists.")
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int = Path(..., ge=1),
    current_user: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    _ensure_self_or_admin(current_user, user_id)
    return _get_user_or_404(db, user_id)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    payload: UserUpdate,
    user_id: int = Path(..., ge=1),
    current_user: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    _ensure_self_or_admin(current_user, user_id)
    user = _get_user_or_404(db, user_id)

    if payload.email is not None:
        new_email = payload.email.strip().lower()
        clash = (
            db.query(User)
            .filter(User.email == new_email, User.id != user_id)
            .first()
        )
        if clash is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists.",
            )
        user.email = new_email
    if payload.first_name is not None:
        user.first_name = payload.first_name.strip()
    if payload.last_name is not None:
        user.last_name = payload.last_name.strip()
    if payload.organization is not None:
        user.organization = payload.organization.strip()
    if payload.password is not None:
        user.hashed_password = get_password_hash(payload.password)
    if payload.role_ids is not None:
        # Solo admin puede cambiar roles.
        if current_user.role != UserRole.ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin can change role assignments.",
            )
        _set_role_ids(db, user, payload.role_ids)
    if getattr(payload, "phone", None) is not None:
        user.phone = payload.phone.strip()

    db.add(user)
    safe_commit(db, conflict_detail="A user with this email already exists.")
    db.refresh(user)
    return user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_user(
    user_id: int = Path(..., ge=1),
    current_user: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    _ensure_self_or_admin(current_user, user_id)
    user = _get_user_or_404(db, user_id)
    db.delete(user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
