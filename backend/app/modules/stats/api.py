"""Endpoints CRUD de Stats alineados con la API oficial.

- GET    /api/v1/stats
- POST   /api/v1/stats
- GET    /api/v1/stats/{stats_id}
- PUT    /api/v1/stats/{stats_id}
- DELETE /api/v1/stats/{stats_id}
"""

from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_verified_user, get_db
from app.modules.auth.models import User
from app.modules.alerts.models import Alert
from app.modules.news.models import News
from app.modules.sources.models import InformationSource, RSSChannel
from app.modules.stats.models import Stats
from app.modules.stats.schemas import StatsCreate, StatsResponse, StatsUpdate

router = APIRouter(prefix="/stats", tags=["stats"])


def _get_stats_or_404(db: Session, stats_id: int) -> Stats:
    stats = db.query(Stats).filter(Stats.id == stats_id).first()
    if stats is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stats not found.",
        )
    return stats


def _normalize_metrics(metrics) -> list[dict]:
    cleaned: list[dict] = []
    seen_names: set[str] = set()
    for entry in metrics or []:
        if hasattr(entry, "model_dump"):
            data = entry.model_dump()
        elif isinstance(entry, dict):
            data = entry
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Each metric must be an object with 'name' and 'value'.",
            )
        name = (data.get("name") or "").strip()
        value = data.get("value")
        if not name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Metric name cannot be empty.",
            )
        if value is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Metric '{name}' must have a numeric value.",
            )
        if len(name) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Metric name must not exceed 100 characters.",
            )
        try:
            value = float(value)
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Metric '{name}' value must be numeric.",
            )
        name_lower = name.lower()
        if name_lower in seen_names:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Duplicate metric name: '{name}'.",
            )
        seen_names.add(name_lower)
        cleaned.append({"name": name, "value": value})
    return cleaned


def _category_name(category) -> str:
    if isinstance(category, dict):
        return str(category.get("label") or category.get("name") or category.get("code") or "Sin categoria")
    return str(category or "Sin categoria")


def _sorted_category_counts(counts: dict[str, int]) -> list[dict]:
    return [
        {"category": category, "count": count}
        for category, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


@router.get("", response_model=List[StatsResponse])
def list_stats(
    _: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    return db.query(Stats).order_by(Stats.id).all()


@router.get("/global")
def get_global_stats(
    _: Annotated[User, Depends(get_current_active_verified_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    news_category_rows = (
        db.query(News.category, func.count(News.id))
        .group_by(News.category)
        .all()
    )
    news_category_counts: dict[str, int] = {}
    for category, count in news_category_rows:
        name = _category_name(category)
        news_category_counts[name] = news_category_counts.get(name, 0) + count
    news_by_category = _sorted_category_counts(news_category_counts)

    alert_category_counts: dict[str, int] = {}
    for (categories,) in db.query(Alert.categories).all():
        for category in categories or []:
            name = _category_name(category)
            alert_category_counts[name] = alert_category_counts.get(name, 0) + 1

    total_rss_channels = db.query(RSSChannel).count()
    total_media_outlets = db.query(InformationSource).count()

    return {
        "total_sources": total_rss_channels,
        "total_rss_channels": total_rss_channels,
        "total_media_outlets": total_media_outlets,
        "total_news": db.query(News).count(),
        "news_by_category": news_by_category,
        "total_alerts": db.query(Alert).count(),
        "alerts_by_category": _sorted_category_counts(alert_category_counts),
    }


@router.post(
    "",
    response_model=StatsResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_stats(
    payload: StatsCreate,
    _: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    stats = Stats(metrics=_normalize_metrics(payload.metrics))
    db.add(stats)
    db.commit()
    db.refresh(stats)
    return stats


@router.get("/{stats_id}", response_model=StatsResponse)
def get_stats(
    stats_id: int = Path(..., ge=1),
    _: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    return _get_stats_or_404(db, stats_id)


@router.put("/{stats_id}", response_model=StatsResponse)
def update_stats(
    payload: StatsUpdate,
    stats_id: int = Path(..., ge=1),
    _: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    stats = _get_stats_or_404(db, stats_id)
    if payload.metrics is not None:
        stats.metrics = _normalize_metrics(payload.metrics)
    db.add(stats)
    db.commit()
    db.refresh(stats)
    return stats


@router.delete(
    "/{stats_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_stats(
    stats_id: int = Path(..., ge=1),
    _: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    stats = _get_stats_or_404(db, stats_id)
    db.delete(stats)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
