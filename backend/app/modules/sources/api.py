"""APIs alineadas con la API oficial:

- ``/api/v1/categories``: CRUD de Category.
- ``/api/v1/information-sources``: CRUD de InformationSource.
- ``/api/v1/information-sources/{source_id}/rss-channels``: CRUD anidado de RSSChannel.

Endpoints añadidos sobre el contrato oficial (permitido por el profesor):
- ``GET /api/v1/information-sources/catalog/summary``: resumen del catálogo
  para el dashboard (cumple checklist #13-15).
- ``PATCH /api/v1/information-sources/{source_id}/rss-channels/{channel_id}/activate``
- ``PATCH /api/v1/information-sources/{source_id}/rss-channels/{channel_id}/deactivate``

Permisos:
- Lectura: cualquier usuario autenticado y verificado.
- Escritura: ``gestor`` o ``admin``.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_verified_user, get_db, require_role
from app.core.iptc import IPTC_CATEGORY_CODES
from app.modules.auth.models import User
from app.modules.auth.schemas import UserRole
from app.modules.sources.models import Category, InformationSource, RSSChannel
from app.modules.sources.schemas import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    InformationSourceCreate,
    InformationSourceResponse,
    InformationSourceUpdate,
    RSSChannelCreate,
    RSSChannelResponse,
    RSSChannelUpdate,
    SourceCatalogSummaryResponse,
)


_gestor_or_admin = require_role(UserRole.ADMIN, UserRole.GESTOR)


# ─────────────────────────────────────────────────────────────────────
# Categories
# ─────────────────────────────────────────────────────────────────────

categories_router = APIRouter(prefix="/categories", tags=["categories"])


def _get_category_or_404(db: Session, category_id: int) -> Category:
    category = db.query(Category).filter(Category.id == category_id).first()
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found.",
        )
    return category


@categories_router.get("", response_model=List[CategoryResponse])
def list_categories(
    _: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
) -> List[Category]:
    return db.query(Category).order_by(Category.id).all()


@categories_router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_category(
    payload: CategoryCreate,
    _: User = Depends(_gestor_or_admin),
    db: Session = Depends(get_db),
) -> Category:
    name = payload.name.strip()
    existing = db.query(Category).filter(Category.name == name).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A category with this name already exists.",
        )
    category = Category(name=name, source=payload.source)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@categories_router.get("/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: int = Path(..., ge=1),
    _: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
) -> Category:
    return _get_category_or_404(db, category_id)


@categories_router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    payload: CategoryUpdate,
    category_id: int = Path(..., ge=1),
    _: User = Depends(_gestor_or_admin),
    db: Session = Depends(get_db),
) -> Category:
    category = _get_category_or_404(db, category_id)
    if payload.name is not None:
        new_name = payload.name.strip()
        clash = (
            db.query(Category)
            .filter(Category.name == new_name, Category.id != category_id)
            .first()
        )
        if clash is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A category with this name already exists.",
            )
        category.name = new_name
    if payload.source is not None:
        category.source = payload.source
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@categories_router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_category(
    category_id: int = Path(..., ge=1),
    _: User = Depends(_gestor_or_admin),
    db: Session = Depends(get_db),
) -> Response:
    category = _get_category_or_404(db, category_id)
    if category.rss_channels:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete a category that has RSS channels assigned.",
        )
    db.delete(category)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ─────────────────────────────────────────────────────────────────────
# Information Sources + nested RSS Channels
# ─────────────────────────────────────────────────────────────────────

information_sources_router = APIRouter(
    prefix="/information-sources",
    tags=["information-sources"],
)


def _get_information_source_or_404(db: Session, source_id: int) -> InformationSource:
    source = db.query(InformationSource).filter(InformationSource.id == source_id).first()
    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Information source not found.",
        )
    return source


def _get_rss_channel_or_404(db: Session, source_id: int, channel_id: int) -> RSSChannel:
    channel = (
        db.query(RSSChannel)
        .filter(
            RSSChannel.id == channel_id,
            RSSChannel.information_source_id == source_id,
        )
        .first()
    )
    if channel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RSS channel not found for this information source.",
        )
    return channel


def _ensure_category_exists(db: Session, category_id: int) -> Category:
    category = db.query(Category).filter(Category.id == category_id).first()
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category with id {category_id} does not exist.",
        )
    return category


# ── Catalog summary (endpoint añadido) ───────────────────────────────


@information_sources_router.get(
    "/catalog/summary",
    response_model=SourceCatalogSummaryResponse,
)
def get_catalog_summary(
    _: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
) -> dict:
    total_channels = db.query(RSSChannel).count()
    total_media_outlets = db.query(InformationSource).count()
    iptc_codes = set(IPTC_CATEGORY_CODES)
    covered_codes = {
        row[0]
        for row in db.query(Category.name)
        .join(RSSChannel, RSSChannel.category_id == Category.id)
        .all()
    }
    iptc_categories_covered = len(covered_codes & iptc_codes)
    return {
        "total_channels": total_channels,
        "total_media_outlets": total_media_outlets,
        "iptc_categories_covered": iptc_categories_covered,
        "iptc_categories_total": len(iptc_codes),
        "covers_all_iptc_categories": iptc_codes.issubset(covered_codes),
    }


# ── InformationSource CRUD ──────────────────────────────────────────


@information_sources_router.get("", response_model=List[InformationSourceResponse])
def list_information_sources(
    _: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
) -> List[InformationSource]:
    return (
        db.query(InformationSource)
        .order_by(InformationSource.name.asc())
        .all()
    )


@information_sources_router.post(
    "",
    response_model=InformationSourceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_information_source(
    payload: InformationSourceCreate,
    _: User = Depends(_gestor_or_admin),
    db: Session = Depends(get_db),
) -> InformationSource:
    source = InformationSource(name=payload.name.strip(), url=str(payload.url))
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@information_sources_router.get(
    "/{source_id}",
    response_model=InformationSourceResponse,
)
def get_information_source(
    source_id: int = Path(..., ge=1),
    _: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
) -> InformationSource:
    return _get_information_source_or_404(db, source_id)


@information_sources_router.put(
    "/{source_id}",
    response_model=InformationSourceResponse,
)
def update_information_source(
    payload: InformationSourceUpdate,
    source_id: int = Path(..., ge=1),
    _: User = Depends(_gestor_or_admin),
    db: Session = Depends(get_db),
) -> InformationSource:
    source = _get_information_source_or_404(db, source_id)
    if payload.name is not None:
        source.name = payload.name.strip()
    if payload.url is not None:
        source.url = str(payload.url)
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@information_sources_router.delete(
    "/{source_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_information_source(
    source_id: int = Path(..., ge=1),
    _: User = Depends(_gestor_or_admin),
    db: Session = Depends(get_db),
) -> Response:
    source = _get_information_source_or_404(db, source_id)
    db.delete(source)  # cascade borra rss_channels asociados
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── RSSChannel CRUD anidado ─────────────────────────────────────────


@information_sources_router.get(
    "/{source_id}/rss-channels",
    response_model=List[RSSChannelResponse],
)
def list_rss_channels(
    source_id: int = Path(..., ge=1),
    _: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
) -> List[RSSChannel]:
    _get_information_source_or_404(db, source_id)
    return (
        db.query(RSSChannel)
        .filter(RSSChannel.information_source_id == source_id)
        .order_by(RSSChannel.id)
        .all()
    )


@information_sources_router.post(
    "/{source_id}/rss-channels",
    response_model=RSSChannelResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_rss_channel(
    payload: RSSChannelCreate,
    source_id: int = Path(..., ge=1),
    _: User = Depends(_gestor_or_admin),
    db: Session = Depends(get_db),
) -> RSSChannel:
    _get_information_source_or_404(db, source_id)
    _ensure_category_exists(db, payload.category_id)
    channel = RSSChannel(
        url=str(payload.url),
        category_id=payload.category_id,
        information_source_id=source_id,
    )
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return channel


@information_sources_router.get(
    "/{source_id}/rss-channels/{channel_id}",
    response_model=RSSChannelResponse,
)
def get_rss_channel(
    source_id: int = Path(..., ge=1),
    channel_id: int = Path(..., ge=1),
    _: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
) -> RSSChannel:
    return _get_rss_channel_or_404(db, source_id, channel_id)


@information_sources_router.put(
    "/{source_id}/rss-channels/{channel_id}",
    response_model=RSSChannelResponse,
)
def update_rss_channel(
    payload: RSSChannelUpdate,
    source_id: int = Path(..., ge=1),
    channel_id: int = Path(..., ge=1),
    _: User = Depends(_gestor_or_admin),
    db: Session = Depends(get_db),
) -> RSSChannel:
    channel = _get_rss_channel_or_404(db, source_id, channel_id)
    if payload.url is not None:
        channel.url = str(payload.url)
    if payload.category_id is not None:
        _ensure_category_exists(db, payload.category_id)
        channel.category_id = payload.category_id
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return channel


@information_sources_router.delete(
    "/{source_id}/rss-channels/{channel_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_rss_channel(
    source_id: int = Path(..., ge=1),
    channel_id: int = Path(..., ge=1),
    _: User = Depends(_gestor_or_admin),
    db: Session = Depends(get_db),
) -> Response:
    channel = _get_rss_channel_or_404(db, source_id, channel_id)
    db.delete(channel)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Activate / deactivate (endpoint añadido) ─────────────────────────


@information_sources_router.patch(
    "/{source_id}/rss-channels/{channel_id}/activate",
    response_model=RSSChannelResponse,
)
def activate_rss_channel(
    source_id: int = Path(..., ge=1),
    channel_id: int = Path(..., ge=1),
    _: User = Depends(_gestor_or_admin),
    db: Session = Depends(get_db),
) -> RSSChannel:
    channel = _get_rss_channel_or_404(db, source_id, channel_id)
    channel.is_active = True
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return channel


@information_sources_router.patch(
    "/{source_id}/rss-channels/{channel_id}/deactivate",
    response_model=RSSChannelResponse,
)
def deactivate_rss_channel(
    source_id: int = Path(..., ge=1),
    channel_id: int = Path(..., ge=1),
    _: User = Depends(_gestor_or_admin),
    db: Session = Depends(get_db),
) -> RSSChannel:
    channel = _get_rss_channel_or_404(db, source_id, channel_id)
    channel.is_active = False
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return channel


# Router unificado para registrar en api.router
def get_routers() -> list[APIRouter]:
    return [categories_router, information_sources_router]
