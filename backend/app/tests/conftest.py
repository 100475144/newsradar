"""
Pytest fixtures para el backend de NewsRadar.

⚠️ BLINDAJE DE SEGURIDAD:
Este fichero refuerza que los tests NUNCA puedan correr accidentalmente contra
la base de datos de producción/desarrollo. La regla es simple: la URL de la
BD apuntada por DATABASE_URL debe contener la palabra "test" en el nombre de
la base de datos. Si no, abortamos antes de tocar nada (sin crear/dropar tablas).

Esto evita el escenario "alguien ejecuta pytest dentro del contenedor backend
con la DATABASE_URL de producción y nos dropa todas las tablas".
"""

from os import getenv
from urllib.parse import urlparse

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.deps import get_db
from app.core.database import Base
from app.main import app

# ─────────────────────────────────────────────────────────────────────
# Blindaje: la BD de tests debe tener "test" en el nombre.
# ─────────────────────────────────────────────────────────────────────
TEST_DATABASE_URL = getenv("DATABASE_URL")

if not TEST_DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Tests require an explicit DATABASE_URL "
        "pointing to a test database (its name must contain 'test')."
    )


def _is_test_database_url(url: str) -> bool:
    """La BD apuntada debe llamarse de forma que contenga 'test'."""
    try:
        parsed = urlparse(url)
    except Exception:
        return False

    # Para URLs SQLite en memoria o ficheros locales también aceptamos.
    if parsed.scheme.startswith("sqlite"):
        return True

    db_name = (parsed.path or "").lstrip("/")
    return "test" in db_name.lower()


if not _is_test_database_url(TEST_DATABASE_URL):
    raise RuntimeError(
        f"Refusing to run tests against a non-test database: {TEST_DATABASE_URL!r}.\n"
        "Set DATABASE_URL to a database whose name contains 'test' "
        "(e.g. postgresql+psycopg://user:pass@localhost:5432/newsradar_test)."
    )


engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


# Crear tablas antes de tests
@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# Sesión por test (aislamiento)
@pytest.fixture
def db():
    connection = engine.connect()
    transaction = connection.begin()

    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# Override de dependencia FastAPI
@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c
