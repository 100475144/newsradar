import logging
from datetime import datetime, timezone

from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.modules.auth.repository import UserRepository
from app.modules.auth.schemas import LoginResponse, UserCreate
from app.modules.notifications.email_utils import (
    send_password_reset_email,
    send_verification_email,
)

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    def register_user(self, user_data: UserCreate):
        existing_user = self.repository.get_by_email(user_data.email)
        if existing_user:
            raise ValueError("A user with this email already exists.")

        hashed_password = get_password_hash(user_data.password)
        user = self.repository.create(user_data, hashed_password)

        # Generate verification token and send email
        token_obj = self.repository.create_verification_token(user.id)
        email_sent = send_verification_email(user.email, token_obj.token)
        if not email_sent:
            logger.warning(
                "Verification email could not be sent to %s (SMTP may not be configured).",
                user.email,
            )

        return user

    def verify_email(self, token: str):
        token_obj = self.repository.get_verification_token(token)
        if token_obj is None:
            raise ValueError("Invalid verification token.")

        if token_obj.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            self.repository.delete_verification_token(token_obj)
            raise ValueError("Verification token has expired. Please request a new one.")

        user = self.repository.get_by_id(token_obj.user_id)
        if user is None:
            raise ValueError("User not found.")

        self.repository.update(user, is_verified=True)
        self.repository.delete_verification_token(token_obj)
        return user

    def resend_verification_email(self, email: str):
        user = self.repository.get_by_email(email)
        if user is None:
            raise ValueError("User not found.")
        if user.is_verified:
            raise ValueError("Email is already verified.")

        token_obj = self.repository.create_verification_token(user.id)
        email_sent = send_verification_email(user.email, token_obj.token)
        if not email_sent:
            logger.warning(
                "Verification email could not be sent to %s (SMTP may not be configured).",
                user.email,
            )
        return user

    def request_password_reset(self, email: str) -> None:
        user = self.repository.get_by_email(email)
        if user is None:
            # Do not disclose whether the email exists.
            return
        if hasattr(user, "is_active") and not user.is_active:
            return

        token_obj = self.repository.create_password_reset_token(user.id)
        email_sent = send_password_reset_email(user.email, token_obj.token)
        if not email_sent:
            logger.warning(
                "Password reset email could not be sent to %s (SMTP may not be configured).",
                user.email,
            )

    def reset_password(self, token: str, password: str):
        token_obj = self.repository.get_password_reset_token(token)
        if token_obj is None:
            raise ValueError("Invalid password reset token.")

        if token_obj.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            self.repository.delete_password_reset_token(token_obj)
            raise ValueError("Password reset token has expired. Please request a new one.")

        user = self.repository.get_by_id(token_obj.user_id)
        if user is None:
            raise ValueError("User not found.")

        self.repository.update(user, hashed_password=get_password_hash(password))
        self.repository.delete_password_reset_token(token_obj)
        return user

    def validate_user_credentials(self, email: str, password: str):
        user = self.repository.get_by_email(email)
        if not user:
            raise ValueError("Invalid email or password.")

        if not verify_password(password, user.hashed_password):
            raise ValueError("Invalid email or password.")

        if hasattr(user, "is_active") and not user.is_active:
            raise ValueError("This user account is inactive.")

        if hasattr(user, "is_verified") and not user.is_verified:
            raise ValueError(
                "Email not verified. Please verify your email before signing in."
            )

        return user

    def login_user(self, email: str, password: str) -> LoginResponse:
        user = self.validate_user_credentials(email, password)

        access_token = create_access_token(subject=user.id)

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=user,
        )

    def get_user_by_id(self, user_id: int):
        user = self.repository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found.")
        return user
