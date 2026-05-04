from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import (
    get_current_active_verified_user,
    get_db,
    require_role,
)
from app.modules.auth.models import User
from app.modules.auth.repository import UserRepository
from app.modules.auth.schemas import (
    ForgotPasswordRequest,
    MessageResponse,
    ResetPasswordRequest,
    Token,
    LoginResponse,
    RegisterResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    UserRole,
)
from app.modules.auth.service import AuthService


router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Build the auth service with its database-backed repository."""
    repository = UserRepository(db)
    return AuthService(repository)

@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
) -> RegisterResponse:
    """Register a new user account. A verification email will be sent."""
    try:
        user = auth_service.register_user(user_data)
        return RegisterResponse(
            message="User registered successfully. Please check your email to verify your account.",
            user=user,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/verify-email",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
def verify_email(
    token: str = Query(..., description="Email verification token"),
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    """Verify a user's email address using the token sent by email."""
    try:
        auth_service.verify_email(token)
        return MessageResponse(message="Email verified successfully. You can now log in.")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/resend-verification",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
def resend_verification(
    email: str = Query(..., description="Email address to resend verification to"),
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    """Resend the verification email (generates a new token, old one is invalidated)."""
    try:
        auth_service.resend_verification_email(email)
        return MessageResponse(message="Verification email sent. The link expires in 24 hours.")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/forgot-password",
    status_code=status.HTTP_200_OK,
)
def forgot_password(
    payload: ForgotPasswordRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> MessageResponse:
    """Send a password reset email when the account exists."""
    auth_service.request_password_reset(payload.email)
    return MessageResponse(
        message="If the email exists, a password reset link has been sent.",
    )


@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
)
def reset_password(
    payload: ResetPasswordRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> MessageResponse:
    """Reset a password using a valid password reset token."""
    try:
        auth_service.reset_password(payload.token, payload.password)
        return MessageResponse(message="Password updated successfully. You can now sign in.")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
)
def login(
    credentials: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    """Authenticate a user and return an access token."""
    try:
        return auth_service.login_user(
            email=credentials.email,
            password=credentials.password,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


@router.post(
    "/token",
    response_model=Token,
    status_code=status.HTTP_200_OK,
)
def login_for_oauth2(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
) -> Token:
    """OAuth2-compatible token endpoint for Swagger/UI authorization."""
    try:
        login_response = auth_service.login_user(
            email=form_data.username,
            password=form_data.password,
        )
        return Token(
            access_token=login_response.access_token,
            token_type=login_response.token_type,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
def read_current_user(
    current_user: User = Depends(get_current_active_verified_user),
) -> UserResponse:
    """Return the currently authenticated and verified user."""
    return current_user


# ── Admin-only: user management ──────────────────────────────────────

@router.get(
    "/users",
    response_model=list[UserResponse],
    status_code=status.HTTP_200_OK,
)
def list_users(
    _admin: User = Depends(require_role(UserRole.ADMIN)),
    auth_service: AuthService = Depends(get_auth_service),
) -> list[UserResponse]:
    """List all users (admin only)."""
    return auth_service.repository.list_all()


@router.patch(
    "/users/{user_id}/role",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
def change_user_role(
    user_id: int,
    role: UserRole = Query(..., description="New role to assign"),
    _admin: User = Depends(require_role(UserRole.ADMIN)),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """Change a user's role (admin only)."""
    try:
        user = auth_service.get_user_by_id(user_id)
        updated = auth_service.repository.update(user, role=role.value)
        return updated
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
