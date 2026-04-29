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
    """Stats globales del sistema (no per-user)."""
    return service.get_stats()


@router.get("/wordcloud")
def news_wordcloud(
    category: str | None = Query(default=None),
    limit: int = Query(default=50, ge=10, le=200),
    current_user: User = Depends(get_current_active_verified_user),
    service: NewsService = Depends(get_news_service),
):
    """Wordcloud globales (no per-user)."""
    return service.get_wordcloud(category=category, limit=limit)


# ── Per-user (CAMBIO #2: dashboards solo con datos del user logueado) ─


@router.get("/me/stats")
def my_news_stats(
    current_user: User = Depends(get_current_active_verified_user),
    service: NewsService = Depends(get_news_service),
):
    """Stats de noticias matcheadas por las alertas del usuario logueado.

    Las "noticias del usuario" se computan a partir de las notificaciones
    generadas por el motor de matching: ``news ↔ notification ↔ user``.
    """
    return service.get_stats_for_user(current_user.id)


@router.get("/me/wordcloud")
def my_news_wordcloud(
    category: str | None = Query(default=None),
    limit: int = Query(default=50, ge=10, le=200),
    current_user: User = Depends(get_current_active_verified_user),
    service: NewsService = Depends(get_news_service),
):
    """Wordcloud calculada SOLO con las noticias matcheadas por las alertas
    del usuario logueado (CAMBIO #2 del enunciado, duda 21-abr y 28-abr)."""
    return service.get_wordcloud_for_user(
        user_id=current_user.id,
        category=category,
        limit=limit,
    )


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
