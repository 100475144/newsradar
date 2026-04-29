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
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    organization: Optional[str] = Field(default=None, max_length=150)

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_names(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be empty or blank.")
        return value

    @field_validator("organization")
    @classmethod
    def validate_organization(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        return value or None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long.")
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


class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    organization: Optional[str] = Field(default=None, max_length=150)

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
        return value or None


class UserResponse(UserBase):
    id: int
    role: UserRole = UserRole.GESTOR
    role_ids: List[int] = Field(default_factory=list)
    is_active: bool = True
    is_verified: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ── Roles (entidad propia, alineada con la API oficial) ──────────────


class RoleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)


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