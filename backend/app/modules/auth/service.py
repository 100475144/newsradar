from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.modules.auth.repository import UserRepository
from app.modules.auth.schemas import LoginResponse, UserCreate


class AuthService:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    def register_user(self, user_data: UserCreate):
        existing_user = self.repository.get_by_email(user_data.email)
        if existing_user:
            raise ValueError("A user with this email already exists.")

        hashed_password = get_password_hash(user_data.password)
        user = self.repository.create(user_data, hashed_password)
        return user

    def validate_user_credentials(self, email: str, password: str):
        user = self.repository.get_by_email(email)
        if not user:
            raise ValueError("Invalid email or password.")

        if not verify_password(password, user.hashed_password):
            raise ValueError("Invalid email or password.")

        if hasattr(user, "is_active") and not user.is_active:
            raise ValueError("This user account is inactive.")

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