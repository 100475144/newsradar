"""Utilidades transversales sobre la sesión de SQLAlchemy.

``safe_commit`` traduce las violaciones de constraints UNIQUE (que pueden
ocurrir bajo carrera entre workers) en respuestas HTTP 409 en vez de dejar
que la excepción se propague y se convierta en un 500 genérico.

Esto es necesario porque los endpoints como ``POST /users`` y ``POST /roles``
hacen un patrón típico SELECT-then-INSERT que NO es atómico: dos requests
concurrentes pueden ambas ver "no existe" en el SELECT y luego intentar el
INSERT — sólo una lo consigue y la otra recibe ``UniqueViolation`` de la BD.
La BD garantiza la integridad, pero el código Python tiene que interpretar
ese error correctamente.

Uso típico::

    db.add(obj)
    safe_commit(db, conflict_detail="A user with this email already exists.")
    db.refresh(obj)
"""

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def safe_commit(
    db: Session,
    *,
    conflict_detail: str = "Resource already exists.",
) -> None:
    """Commit transaction, translating UNIQUE constraint violations into 409.

    Otros ``IntegrityError`` (por ejemplo violaciones de FK) se traducen como
    400 con un mensaje genérico — son errores del cliente, no del servidor.
    """
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        original = getattr(exc, "orig", None)
        # ``psycopg.errors.UniqueViolation`` es lo que lanza Postgres cuando
        # un INSERT viola una constraint UNIQUE. Comprobamos por nombre de
        # clase para no depender directamente del módulo psycopg.
        if original is not None and "UniqueViolation" in type(original).__name__:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=conflict_detail,
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database integrity error.",
        ) from exc
