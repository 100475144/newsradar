from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.endpoints import health
from app.modules.auth.api import router as auth_router
from app.modules.auth.roles_api import router as roles_router
from app.modules.sources.api import categories_router, information_sources_router
from app.modules.news.api import router as news_router
from app.modules.crawler.api import router as crawler_router
from app.modules.alerts.api import (
    helpers_router as alerts_helpers_router,
    me_router as alerts_me_router,
    router as alerts_router,
)
from app.modules.notifications.api import router as notifications_router

from .deps import get_db


api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth_router)
api_router.include_router(roles_router)
api_router.include_router(categories_router)
api_router.include_router(information_sources_router)
api_router.include_router(news_router)
api_router.include_router(crawler_router)
api_router.include_router(alerts_helpers_router)
api_router.include_router(alerts_me_router)
api_router.include_router(alerts_router)
api_router.include_router(notifications_router)


@api_router.get("/health/db", tags=["system"])
def health_db(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "service": "database"}
    except Exception as e:
        return {"status": "error", "database_error": str(e)}