import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.auth.models import EmailVerificationToken, Role, User
from app.modules.auth.schemas import UserCreate

# Nombre canónico del rol asignado por defecto a los nuevos usuarios.
# CAMBIO #1bis del enunciado: todo nuevo usuario es "gestor" automáticamente.
DEFAULT_ROLE_NAME = "gestor"


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        normalized_email = email.strip().lower()
        return self.db.query(User).filter(User.email == normalized_email).first()

    def create(self, user_data: UserCreate, hashed_password: str) -> User:
        user = User(
            email=user_data.email.strip().lower(),
            first_name=user_data.first_name.strip(),
            last_name=user_data.last_name.strip(),
            organization=user_data.organization.strip() if user_data.organization else None,
            hashed_password=hashed_password,
        )
        # CAMBIO #1bis: asignar siempre el rol "gestor" automáticamente.
        gestor_role = self.db.query(Role).filter(Role.name == DEFAULT_ROLE_NAME).first()
        if gestor_role is not None:
            user.roles.append(gestor_role)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user: User, **kwargs) -> User:
        for field, value in kwargs.items():
            setattr(user, field, value)

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def list_all(self) -> list[User]:
        return self.db.query(User).order_by(User.id).all()

    # ── Email verification tokens ────────────────────────────────────

    def create_verification_token(self, user_id: int) -> EmailVerificationToken:
        # Invalidate any existing tokens for this user
        self.db.query(EmailVerificationToken).filter(
            EmailVerificationToken.user_id == user_id
        ).delete()

        token = EmailVerificationToken(
            user_id=user_id,
            token=secrets.token_urlsafe(48),
            expires_at=datetime.now(timezone.utc) + timedelta(
                hours=settings.verification_token_expire_hours
            ),
        )
        self.db.add(token)
        self.db.commit()
        self.db.refresh(token)
        return token

    def get_verification_token(self, token: str) -> Optional[EmailVerificationToken]:
        return (
            self.db.query(EmailVerificationToken)
            .filter(EmailVerificationToken.token == token)
            .first()
        )

    def delete_verification_token(self, token_obj: EmailVerificationToken) -> None:
        self.db.delete(token_obj)
        self.db.commit()