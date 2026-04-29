"""Remove 'lector' role + introduce roles entity (Role + user_roles)

Revision ID: f1a2b3c4d5e6
Revises: efcce35ef89a
Create Date: 2026-04-29 22:00:00.000000

Cambios:
1. Cualquier usuario con rol "lector" pasa a "gestor" (adenda oficial: rol
   "lector" desaparece).
2. Se crea la tabla `roles` y la asociación `user_roles` para alinear el
   modelo con la API oficial (User tiene `role_ids: List[int]`).
3. Se siembran los roles "admin" y "gestor".
4. Backfill: a cada usuario existente se le asocian los role_ids
   correspondientes a su columna `role` actual.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "efcce35ef89a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Convertir lector → gestor
    op.execute("UPDATE users SET role = 'gestor' WHERE role = 'lector'")

    # 2. Tabla roles
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(length=100), nullable=False, unique=True),
    )

    # 3. Tabla de asociación user_roles
    op.create_table(
        "user_roles",
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "role_id",
            sa.Integer(),
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    # 4. Seed de roles canónicos: admin y gestor
    op.execute(
        """
        INSERT INTO roles (id, name) VALUES (1, 'admin')
        ON CONFLICT (id) DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO roles (id, name) VALUES (2, 'gestor')
        ON CONFLICT (id) DO NOTHING
        """
    )

    # Asegurar que la secuencia de roles avance más allá de los IDs sembrados
    op.execute(
        """
        SELECT setval(
            pg_get_serial_sequence('roles', 'id'),
            GREATEST((SELECT COALESCE(MAX(id), 0) FROM roles), 2)
        )
        """
    )

    # 5. Backfill user_roles a partir de la columna role (string) actual.
    op.execute(
        """
        INSERT INTO user_roles (user_id, role_id)
        SELECT u.id, r.id
        FROM users u
        JOIN roles r ON r.name = u.role
        ON CONFLICT DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_table("user_roles")
    op.drop_table("roles")
    # No revertimos el cambio lector → gestor por falta de información.
