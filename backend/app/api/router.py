from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.endpoints import health
from app.modules.auth.api import router as auth_router

from .deps import get_db


api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth_router)


@api_router.get("/health/db", tags=["system"])
def health_db(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "service": "database"}
    except Exception as e:
        return {"status": "error", "database_error": str(e)}