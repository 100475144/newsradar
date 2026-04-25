from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from os import getenv

db_url = getenv("DATABASE_URL")
# la variable de entorno DATABASE_URL se define en 
# docker-compose.yaml

if db_url is None:
    print("[ERROR] DATABASE_URL env variable is not defined")
    exit(-1)

# Engine es el objeto que gestiona la conexión con la base de datos 
engine = create_engine(
    url=db_url, 
    echo=False,   # Mostrar queries en consola, en producción -> False
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True
)

session_newsradar = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)  # Crear sesión con la base de datos

# Base declarativa a usar 
class Base(DeclarativeBase):
    pass

