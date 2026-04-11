from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.endpoints import health
from app.modules.auth.api import router as auth_router
from app.modules.sources.api import router as sources_router
from app.modules.news.api import router as news_router
from app.modules.crawler.api import router as crawler_router
from app.modules.alerts.api import router as alerts_router
from app.modules.notifications.api import router as notifications_router

from .deps import get_db


api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth_router)
api_router.include_router(sources_router)
api_router.include_router(news_router)
api_router.include_router(crawler_router)
api_router.include_router(alerts_router)
api_router.include_router(notifications_router)


@api_router.get("/health/db", tags=["system"])
def health_db(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "service": "database"}
    except Exception as e:
        return {"status": "error", "database_error": str(e)}