from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import session_newsradar
from app.core.security import verify_token
from app.modules.auth.repository import UserRepository
from app.modules.auth.service import AuthService


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


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
):
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