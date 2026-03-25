from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from passlib.context import CryptContext

from app.core.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
    subject: str | Any,
    expires_delta: Optional[timedelta] = None,
) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )

    payload = {
        "sub": str(subject),
        "exp": expire,
    }

    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def verify_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        return payload
    except ExpiredSignatureError as exc:
        raise ValueError("Token has expired.") from exc
    except InvalidTokenError as exc:
        raise ValueError("Invalid token.") from exc


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)