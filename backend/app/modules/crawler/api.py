"""API del módulo crawler: se definirán los endpoints para ejecutar, monitorear o disparar procesos de crawling."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_verified_user, get_db
from app.modules.auth.models import User
from app.modules.news.repository import NewsRepository
from app.modules.news.service import NewsService

from .service import CrawlerService

router = APIRouter(prefix="/crawler", tags=["crawler"])


def get_crawler_service(db: Session = Depends(get_db)) -> CrawlerService:
    news_repository = NewsRepository(db)
    news_service = NewsService(news_repository)
    return CrawlerService(db, news_service)


@router.post("/run")
def run_crawler(
    current_user: User = Depends(get_current_active_verified_user),
    service: CrawlerService = Depends(get_crawler_service),
):
    results = service.crawl_all_active_sources(current_user.id)
    return {
        "status": "ok",
        "processed_sources": len(results),
        "results": [result.model_dump() for result in results],
    }
