"""API del módulo news: se definirán los endpoints REST para consultar y gestionar noticias."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_verified_user, get_db
from app.modules.auth.models import User

from .repository import NewsRepository
from .schemas import NewsListResponse, NewsResponse
from .service import NewsService

router = APIRouter(prefix="/news", tags=["news"])


def get_news_service(db: Session = Depends(get_db)) -> NewsService:
    repository = NewsRepository(db)
    return NewsService(repository)


@router.get("", response_model=NewsListResponse)
def list_news(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    source_id: int | None = Query(default=None),
    category: str | None = Query(default=None),
    current_user: User = Depends(get_current_active_verified_user),
    service: NewsService = Depends(get_news_service),
):
    result = service.list_news(
        skip=skip,
        limit=limit,
        source_id=source_id,
        category=category,
    )
    return NewsListResponse(items=result["items"], total=result["total"])


@router.get("/stats")
def news_stats(
    current_user: User = Depends(get_current_active_verified_user),
    service: NewsService = Depends(get_news_service),
):
    return service.get_stats()


@router.get("/wordcloud")
def news_wordcloud(
    category: str | None = Query(default=None),
    limit: int = Query(default=50, ge=10, le=200),
    current_user: User = Depends(get_current_active_verified_user),
    service: NewsService = Depends(get_news_service),
):
    return service.get_wordcloud(category=category, limit=limit)


@router.get("/{news_id}", response_model=NewsResponse)
def get_news(
    news_id: int,
    current_user: User = Depends(get_current_active_verified_user),
    service: NewsService = Depends(get_news_service),
):
    news = service.get_news(news_id)
    if not news:
        raise HTTPException(status_code=404, detail="News not found")
    return news
