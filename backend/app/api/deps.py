from typing import Generator
from ..core.database import session_newsradar
from sqlalchemy.orm import Session


def get_db() -> Generator[Session, None, None]:
    """
    Obtener una sesión a la base de datos con cleanup automático
    La sesión se cierra tras ejecutar el bloque de código desde 
    el que se haya hecho la llamada a esta función. 

    Para usar get_db() en un endpoint de fastAPI:  
    def endpoint(db: Session = Depends(get_db)):
    
    En Sprint 0.3 / Sprint 1 se conectará a SQLAlchemy Session.
    """
    db = session_newsradar()
    try:
        yield db
    finally:
        db.close()


def get_current_user():
    """
    Placeholder de autenticación.
    En Sprint 1 devolverá el usuario autenticado.
    """
    return None