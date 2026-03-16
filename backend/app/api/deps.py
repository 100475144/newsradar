from typing import Generator


def get_db() -> Generator[None, None, None]:
    """
    Placeholder de dependencia de base de datos.
    En Sprint 0.3 / Sprint 1 se conectará a SQLAlchemy Session.
    """
    yield None


def get_current_user():
    """
    Placeholder de autenticación.
    En Sprint 1 devolverá el usuario autenticado.
    """
    return None