from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserRole(str, Enum):
    """Roles del sistema.

    El rol "lector" se eliminó por adenda oficial al enunciado: todos los nuevos
    usuarios son "gestor" automáticamente. El rol "admin" se mantiene para
    permitir asignaciones via los endpoints de administración (CAMBIO #1).
    """

    ADMIN = "admin"
    GESTOR = "gestor"


class UserBase(BaseModel):
    """Modelo oficial alineado con ``main.py`` del aula global.

    - ``first_name`` / ``last_name`` max 120.
    - ``organization`` OBLIGATORIO max 180 (T6.7).
    - ``role_ids`` se incluye en respuestas pero no se acepta en el body de
      registro (CAMBIO #1bis: el rol gestor se asigna automáticamente).
    """

    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=120)
    last_name: str = Field(..., min_length=1, max_length=120)
    organization: str = Field(..., min_length=1, max_length=180)
    phone: str = Field(..., min_length=9, max_length=9, description="9 numeric digits phone number")

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_names(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be empty or blank.")
        # Reject HTML/script tags (XSS prevention).
        import re
        if re.search(r"<\s*script", value, re.IGNORECASE):
            raise ValueError("HTML script tags are not allowed.")
        # Sanitize: strip any HTML tags.
        value = re.sub(r"<[^>]*>", "", value).strip()
        if not value:
            raise ValueError("This field cannot be empty after sanitization.")
        return value

    @field_validator("organization")
    @classmethod
    def validate_organization(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Organization is required.")
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Phone number is required.")
        if not value.isdigit() or len(value) != 9:
            raise ValueError("Phone number must be exactly 9 numeric digits.")
        return value


class UserCreate(UserBase):
    # Min 6 caracteres como exige la API oficial.
    password: str = Field(..., min_length=6, max_length=128)
    role_ids: Optional[List[int]] = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 6:
            raise ValueError("Password must be at least 6 characters long.")
        return value


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Password cannot be empty.")
        return value


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=1)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("token")
    @classmethod
    def validate_token(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Reset token cannot be empty.")
        return value

    @field_validator("password")
    @classmethod
    def validate_reset_password(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        return value


class UserUpdate(BaseModel):
    """Schema oficial de PUT /users/{id}.

    Todos los campos son opcionales; el cliente solo envía lo que cambia.
    """

    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    organization: Optional[str] = Field(default=None, min_length=1, max_length=180)
    phone: Optional[str] = Field(default=None, min_length=9, max_length=9)
    role_ids: Optional[List[int]] = None
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_optional_names(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be empty or blank.")
        return value

    @field_validator("organization")
    @classmethod
    def validate_optional_organization(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Organization cannot be empty.")
        return value

    @field_validator("phone")
    @classmethod
    def validate_optional_phone(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not value.isdigit() or len(value) != 9:
            raise ValueError("Phone number must be exactly 9 numeric digits.")
        return value


class UserResponse(UserBase):
    id: int
    phone: str
    role: str = UserRole.GESTOR.value
    role_ids: List[int] = Field(default_factory=list)
    is_active: bool = True
    is_verified: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ── Roles (entidad propia, alineada con la API oficial) ──────────────


class RoleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=90)


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=90)


class RoleResponse(RoleBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenWithUser(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenPayload(BaseModel):
    sub: str
    exp: Optional[int] = None


class MessageResponse(BaseModel):
    message: str


class RegisterResponse(BaseModel):
    message: str
    user: UserResponse


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
