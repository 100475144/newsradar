from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from .deps import get_db

api_router = APIRouter()


@api_router.get("/health", tags=["health"])
def health_check() -> dict:
    return {
        "status": "ok",
        "service": "backend",
    }

@api_router.get("/health/db", tags=["health"])
def health_db(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "service": "database"}
    except Exception as e:
        return {"status": "error", "database_error": str(e)}