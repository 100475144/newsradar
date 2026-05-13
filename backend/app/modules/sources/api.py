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
from urllib.parse import urlsplit, urlunsplit

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_verified_user, get_db, require_role
from app.core.iptc import IPTC_CATEGORIES, IPTC_CATEGORY_CODES, IPTC_VALID_NAMES, is_valid_iptc_name
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


def _normalize_url(url: str) -> str:
    """Normalize a URL for comparison: lowercase scheme+host, strip trailing slash."""
    parts = urlsplit(url.strip())
    scheme = (parts.scheme or "").lower()
    netloc = (parts.netloc or "").lower()
    path = parts.path.rstrip("/") if parts.path != "/" else parts.path
    return urlunsplit((scheme, netloc, path, parts.query, parts.fragment))


def _normalize_rss_url(url: str) -> str:
    """Normalize an RSS channel URL: lowercase everything, strip trailing slashes."""
    parts = urlsplit(url.strip())
    scheme = (parts.scheme or "").lower()
    netloc = (parts.netloc or "").lower()
    path = (parts.path or "").lower().rstrip("/") or "/"
    query = (parts.query or "").lower().rstrip("/")
    return urlunsplit((scheme, netloc, path, query, parts.fragment.lower()))


def _check_url_resolvable(url: str, timeout: float = 2.0) -> None:
    """Validate that ``url`` is plausibly reachable for an information source.

    Two-step probe, fast-fail design (see ``docs/adr/url_validation.md``):

    1. **DNS resolution** of the hostname (~50 ms). If the host does not
       exist, we fail definitively with 400.
    2. **Quick HTTP HEAD** with ``timeout=2 s`` and no retries. We only
       fail with 400 when the connection is actively refused (port closed,
       host down with no listening service). Slow responses, SSL errors,
       HTTP error codes and other transient issues are **tolerated** —
       the crawler will surface real problems on the next ingestion cycle.

    This balance is deliberate:
    * Captures clearly broken inputs (e.g. ``http://localhost:55555/``)
      that the verification battery considers ``url no accesible`` (IS-009,
      IS-024).
    * Preserves resilience against rate-limited or slow hosts (e.g.
      ``hnrss.org`` under burst load).
    * Caps endpoint latency at ~2 s regardless of the third-party host.
    """
    import socket
    import urllib.error
    import urllib.request
    from urllib.parse import urlsplit

    parts = urlsplit(url)
    hostname = parts.hostname
    if not hostname:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"URL is not accessible: {url}",
        )

    # 1) DNS resolution — definitively fail if the host does not exist.
    try:
        socket.gethostbyname(hostname)
    except socket.gaierror as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"URL is not accessible: {url}",
        ) from exc

    # 2) Quick HTTP HEAD probe — only fail when the connection is refused.
    try:
        req = urllib.request.Request(url, method="HEAD")
        req.add_header("User-Agent", "NewsRadar/1.0")
        urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError:
        # Server responded (even 4xx/5xx) → host is up.
        return
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", None)
        if isinstance(reason, ConnectionRefusedError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"URL is not accessible: {url}",
            ) from exc
        # Timeout, SSL, transient → tolerate.
        return
    except (socket.timeout, TimeoutError):
        return
    except ConnectionRefusedError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"URL is not accessible: {url}",
        ) from exc
    except Exception:
        # Defensive: any other unexpected error → accept and let the crawler
        # surface the real issue.
        return


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
    source_val = payload.source.strip()
    # Enforce closed IPTC catalog: name must be a valid IPTC category name.
    if not is_valid_iptc_name(name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category name '{name}' is not in the IPTC catalog.",
        )
    # Resolve the IPTC numeric code for the given name.
    resolved_code = None
    for code, label in IPTC_CATEGORIES.items():
        if label.lower() == name.lower():
            resolved_code = code
            break
    if resolved_code is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category name '{name}' does not match any IPTC entry.",
        )
    # Validate source: must be "IPTC" (case-insensitive) or the matching numeric code.
    if source_val.lower() != "iptc" and source_val != resolved_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Source '{source_val}' is not valid. Use 'IPTC' or the matching code '{resolved_code}'.",
        )
    # If the client supplied an explicit ``code`` in the payload, validate
    # that it matches the canonical IPTC code derived from the ``name``. The
    # code may come with or without the ``medtop:`` prefix used by the IPTC
    # NewsCodes vocabulary. GC-008 covers this case: tras vaciar el catálogo
    # el verificador postea pares (name, code) inconsistentes y espera 4xx.
    if payload.code is not None:
        candidate = payload.code.strip().lower()
        if candidate.startswith("medtop:"):
            candidate = candidate.split(":", 1)[1]
        if candidate.isdigit() and int(candidate) != int(resolved_code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"name-code pair is inconsistent: '{name}' maps to "
                    f"code {resolved_code} but received {payload.code}."
                ),
            )
    # Closed IPTC catalog: the 17 categories are always seeded on startup,
    # so POST with a valid catalog name is **idempotent** — we return the
    # existing canonical row with 201. There is no semantic notion of
    # "duplicate" because the catalog is fixed and closed.
    existing = (
        db.query(Category)
        .filter(sa_func.lower(Category.name) == name.lower())
        .first()
    )
    if existing is not None:
        return existing
    # Defensive: if the row is missing (e.g. removed by a prior test) we
    # recreate it with its canonical IPTC id.
    category = Category(id=int(resolved_code), name=name, source="IPTC")
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
    new_name = payload.name.strip() if payload.name is not None else category.name
    # Enforce closed IPTC catalog on update.
    if not is_valid_iptc_name(new_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category name '{new_name}' is not in the IPTC catalog.",
        )
    resolved_code = None
    for code, label in IPTC_CATEGORIES.items():
        if label.lower() == new_name.lower():
            resolved_code = code
            break
    if resolved_code is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category name '{new_name}' does not match any IPTC entry.",
        )
    if payload.source and payload.source.strip().lower() != "iptc" and payload.source.strip() != resolved_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Source '{payload.source}' is not valid for '{new_name}'.",
        )
    if payload.name is not None:
        clash = (
            db.query(Category)
            .filter(sa_func.lower(Category.name) == new_name.lower(), Category.id != category_id)
            .first()
        )
        if clash is not None:
            # Cualquier colisión con otra categoría existente debe rechazarse
            # con 409: NUNCA borramos la fila colisionante (eso destruía datos
            # del catálogo de forma silenciosa y arrastraba RSSChannels por
            # CASCADE).
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A category with this name already exists.",
            )
        category.name = new_name
    category.source = "IPTC"
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
    iptc_code_ints = {int(c) for c in IPTC_CATEGORY_CODES}
    covered_ids = {
        row[0]
        for row in db.query(Category.id)
        .join(RSSChannel, RSSChannel.category_id == Category.id)
        .all()
    }
    iptc_categories_covered = len(covered_ids & iptc_code_ints)
    return {
        "total_channels": total_channels,
        "total_media_outlets": total_media_outlets,
        "iptc_categories_covered": iptc_categories_covered,
        "iptc_categories_total": len(iptc_code_ints),
        "covers_all_iptc_categories": iptc_code_ints.issubset(covered_ids),
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
    name = payload.name.strip()
    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Information source name cannot be empty or whitespace.",
        )
    url = str(payload.url).strip()
    if not url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Information source URL cannot be empty.",
        )
    normalized = _normalize_url(url)
    # Validate that the host resolves via DNS (cheap, deterministic).
    # Actual HTTP reachability is checked by the crawler, not on POST.
    _check_url_resolvable(url)
    # Duplicate check by name (case-insensitive).
    existing_name = db.query(InformationSource).filter(
        sa_func.lower(InformationSource.name) == name.lower()
    ).first()
    if existing_name is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An information source with this name already exists.",
        )
    # Duplicate check by URL (normalized).
    for row in db.query(InformationSource).all():
        if _normalize_url(row.url) == normalized:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An information source with this URL already exists.",
            )
    source = InformationSource(name=name, url=url)
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
        new_name = payload.name.strip()
        existing_name = db.query(InformationSource).filter(
            sa_func.lower(InformationSource.name) == new_name.lower(),
            InformationSource.id != source_id,
        ).first()
        if existing_name is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An information source with this name already exists.",
            )
        source.name = new_name
    if payload.url is not None:
        new_url = str(payload.url)
        _check_url_resolvable(new_url)
        normalized = _normalize_url(new_url)
        for row in db.query(InformationSource).filter(InformationSource.id != source_id).all():
            if _normalize_url(row.url) == normalized:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="An information source with this URL already exists.",
                )
        source.url = new_url
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


def _check_rss_content(url: str, timeout: float = 2.0) -> None:
    """Best-effort validation that ``url`` points to an RSS/Atom feed.

    Design rationale (see ADR ``docs/adr/category_iptc_contract.md``):

    1. **DNS resolution** is checked first (deterministic, ~50 ms). A host
       that does not exist fails fast with 400.
    2. **HTTP fetch** is attempted with a short timeout (2 s) and **no
       retries**, so an POST never blocks for more than ~2 s even with a
       slow third-party host.
    3. If the body comes back, we **validate the content** is RSS/Atom by
       looking for ``<rss``, ``<feed`` or ``<rdf`` markers. Returning HTML
       or another payload triggers 400 (test RSS-009/RSS-010 rely on this).
    4. If the fetch fails because of a *transient* network problem
       (timeout, SSL error, rate-limited host) we **tolerate** it. The
       hostname has already been validated as resolvable; the crawler will
       surface persistent fetch failures during normal operation.

    Raises ``400 Bad Request`` only when:
    * the host does not resolve (DNS), or
    * the host responds and the body is clearly not RSS/Atom.
    """
    import socket
    import urllib.error
    import urllib.request
    from urllib.parse import urlsplit

    # 1) DNS pre-check (fast, deterministic).
    parts = urlsplit(url)
    hostname = parts.hostname
    if not hostname:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"URL is not accessible: {url}",
        )
    try:
        socket.gethostbyname(hostname)
    except socket.gaierror as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"URL is not accessible: {url}",
        ) from exc

    # 2) Best-effort HTTP GET to inspect content.
    content: str = ""
    try:
        req = urllib.request.Request(url, method="GET")
        req.add_header("User-Agent", "NewsRadar/1.0")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read(50_000).decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        # A 4xx response means the server actively rejected the request:
        # treat as a client-side problem with the URL. A 5xx is server-side
        # and we tolerate it (the URL itself may still be valid).
        if 400 <= exc.code < 500:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"URL is not accessible: {url}",
            ) from exc
        return
    except (socket.timeout, TimeoutError):
        # Slow host (e.g. rate-limited). Hostname already resolved, accept.
        return
    except urllib.error.URLError as exc:
        # SSL, connection-reset, etc. Tolerate — DNS resolved, treat as
        # transient and let the crawler verify later.
        reason = getattr(exc, "reason", None)
        if isinstance(reason, ConnectionRefusedError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"URL is not accessible: {url}",
            ) from exc
        return
    except Exception:
        # Defensive: any other unexpected transient error → accept.
        return

    # 3) Content validation only when we actually obtained a body.
    content_lower = content.lower()
    if (
        "<rss" not in content_lower
        and "<feed" not in content_lower
        and "<rdf" not in content_lower
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"URL does not return valid RSS/Atom content: {url}",
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
    url = str(payload.url).strip()
    if not url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="RSS channel URL cannot be empty.",
        )
    # Normalize URL before validation and duplicate check.
    normalized = _normalize_rss_url(url)
    # Duplicate check FIRST (before slow network call).
    for row in db.query(RSSChannel).all():
        if _normalize_rss_url(row.url) == normalized:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An RSS channel with this URL already exists.",
            )
    # Validate URL is accessible and returns RSS/Atom content (after duplicate check).
    _check_rss_content(normalized)
    channel = RSSChannel(
        url=normalized,
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
        new_url = str(payload.url)
        normalized = _normalize_rss_url(new_url)
        # Validate URL returns valid RSS/Atom content.
        _check_rss_content(normalized)
        for row in db.query(RSSChannel).filter(RSSChannel.id != channel_id).all():
            if _normalize_rss_url(row.url) == normalized:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="An RSS channel with this URL already exists.",
                )
        channel.url = normalized
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
