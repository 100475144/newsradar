"""Endpoints CRUD de Stats alineados con la API oficial.

- GET    /api/v1/stats
- POST   /api/v1/stats
- GET    /api/v1/stats/{stats_id}
- PUT    /api/v1/stats/{stats_id}
- DELETE /api/v1/stats/{stats_id}
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_verified_user, get_db
from app.modules.auth.models import User
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
    for entry in metrics or []:
        if hasattr(entry, "model_dump"):
            data = entry.model_dump()
        elif isinstance(entry, dict):
            data = entry
        else:
            continue
        name = (data.get("name") or "").strip()
        value = data.get("value")
        if not name or value is None:
            continue
        try:
            value = float(value)
        except (TypeError, ValueError):
            continue
        cleaned.append({"name": name, "value": value})
    return cleaned


@router.get("", response_model=List[StatsResponse])
def list_stats(
    _: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    return db.query(Stats).order_by(Stats.id).all()


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
