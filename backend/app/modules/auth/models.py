from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


# Tabla de asociación m:n entre usuarios y roles.
# Necesaria para alinearnos con la API oficial, donde un User tiene `role_ids: List[int]`.
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)


class Role(Base):
    """Rol del sistema. Modelado como entidad propia para alinearnos con la API oficial."""

    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

    users = relationship(
        "User",
        secondary=user_roles,
        back_populates="roles",
    )


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    email = Column(String, unique=True, index=True, nullable=False)

    # Tras T6.7: tamaños alineados con la API oficial.
    first_name = Column(String(120), nullable=False)
    last_name = Column(String(120), nullable=False)
    organization = Column(String(180), nullable=False)

    hashed_password = Column(String, nullable=False)

    # `role` (string) se mantiene durante la transición para no romper checks
    # ya existentes en api/deps.py::require_role. T6.7 lo eliminará al adoptar
    # completamente role_ids.
    role = Column(String, default="gestor", nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    roles = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users",
        lazy="selectin",
    )

    @property
    def role_ids(self) -> list[int]:
        """IDs de los roles asignados al usuario (alinea con la API oficial)."""
        return [role.id for role in (self.roles or [])]


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
