"""
TEST DATABASE SAFETY GUARD

This test suite MUST NEVER run against a production database.

Rules:
- DATABASE_URL must be defined
- DATABASE_URL must not contain any keyword 
  used for development or production databases
- DATABASE_URL must contain 'test'
- If not, execution will be aborted immediately

This prevents accidental data loss in production environments.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import Base
from app.api.deps import get_db

from os import getenv

# URL de DB de test
TEST_DATABASE_URL = getenv("DATABASE_URL")

if not TEST_DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

DB_NAMES = ["news_db", "dev_db"]

for db in DB_NAMES:
    if db in TEST_DATABASE_URL:
        raise RuntimeError("Refusing to run tests against production DB, modify DATABASE_URL env variable")

if "test" not in TEST_DATABASE_URL:
    raise RuntimeError("Refusing to run tests: DATABASE_URL must point to a test database, modify DATABASE_URL env variable")


""" # Crear tablas antes de tests
@pytest.fixture(scope="session", autouse=True)
def setup_database():
    #Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
 """

# Mantener engine y conexión para
# toda la ejecución de los tests
@pytest.fixture(scope="session")
def engine():
    return create_engine(TEST_DATABASE_URL, echo=False)

TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

@pytest.fixture(scope="session")
def connection(engine):
    return engine.connect()


@pytest.fixture
def db(connection):
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()

@pytest.fixture(autouse=True)
def override_db(db):
    """
    Sustituir la dependencia de base de datos dinámicamente
    para que los tests estén usando siempre la sesión que 
    se define en la fixture anterior "db()"
    """
    def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.clear()

# Mantener mismo cliente de test de FastAPI 
# para toda la ejecución de los tests
@pytest.fixture(scope="session")
def client():
    return TestClient(app)


