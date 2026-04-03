from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import get_current_user, get_db
from app.modules.auth.models import User
from app.modules.auth.repository import UserRepository
from app.modules.auth.schemas import (
    Token,
    LoginResponse,
    RegisterResponse,
    UserCreate,
    UserLogin,
    UserResponse,
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
    """Register a new user account."""
    try:
        user = auth_service.register_user(user_data)
        return RegisterResponse(
            message="User registered successfully.",
            user=user,
        )
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
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Return the currently authenticated user."""
    return current_user