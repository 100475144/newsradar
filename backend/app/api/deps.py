from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import session_newsradar
from app.core.security import verify_token
from app.modules.auth.models import User
from app.modules.auth.repository import UserRepository
from app.modules.auth.schemas import UserRole
from app.modules.auth.service import AuthService


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def get_db() -> Generator[Session, None, None]:
    """
    Obtener una sesión a la base de datos con cleanup automático.
    """
    db = session_newsradar()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Obtener el usuario autenticado a partir del JWT.
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = verify_token(token)
        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

    except Exception:
        raise credentials_exception

    repository = UserRepository(db)
    auth_service = AuthService(repository)

    try:
        user = auth_service.get_user_by_id(int(user_id))
    except Exception:
        raise credentials_exception

    return user


def get_current_active_verified_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Usuario autenticado, activo y con email verificado."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account.",
        )
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email before using the application.",
        )
    return current_user


def require_role(*allowed_roles: UserRole):
    """
    Dependency factory: restringe acceso a los roles indicados.
    Uso: Depends(require_role(UserRole.ADMIN, UserRole.GESTOR))
    """
    def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in [r.value for r in allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' does not have permission for this action.",
            )
        return current_user
    return _check