import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.database import session_newsradar
from app.core.logging_config import configure_logging
from app.core.security import get_password_hash
from app.core.seed_sources import get_seed_catalog_summary, seed_default_sources
from app.modules.auth.models import Role, User
from app.modules.crawler.scheduler import (
    CrawlerScheduler,
    get_crawler_cron_expression,
)

logger = logging.getLogger(__name__)


def _ensure_canonical_roles(db) -> None:
    """Asegura que los roles canónicos (admin y gestor) existan en BD.

    La migración Alembic los siembra, pero esto es defensa en profundidad para
    entornos donde se haya creado la BD con `Base.metadata.create_all` (tests
    o despliegues sin migrar)."""
    for role_name in ("admin", "gestor"):
        existing = db.query(Role).filter(Role.name == role_name).first()
        if existing is None:
            db.add(Role(name=role_name))
    db.commit()


def _seed_admin_user() -> None:
    """Create the initial admin user if it does not exist yet."""
    db = session_newsradar()
    try:
        _ensure_canonical_roles(db)

        existing = db.query(User).filter(User.email == settings.admin_email).first()
        if existing:
            # Asegurar que el admin tiene el rol "admin" asociado (defensa en
            # profundidad para BBDD pre-existentes).
            admin_role = db.query(Role).filter(Role.name == "admin").first()
            if admin_role is not None and admin_role not in existing.roles:
                existing.roles.append(admin_role)
                db.commit()
            return

        admin_role = db.query(Role).filter(Role.name == "admin").first()
        admin = User(
            email=settings.admin_email,
            first_name=settings.admin_first_name,
            last_name=settings.admin_last_name,
            organization="NewsRadar",
            hashed_password=get_password_hash(settings.admin_password),
            role="admin",
            is_active=True,
            is_verified=True,
        )
        if admin_role is not None:
            admin.roles.append(admin_role)
        db.add(admin)
        db.commit()
        logger.info("Admin user seeded: %s", settings.admin_email)
    finally:
        db.close()


def _seed_rss_sources() -> None:
    """Ensure every user has the default RSS catalog."""
    db = session_newsradar()
    try:
        inserted_total = seed_default_sources(db)
        summary = get_seed_catalog_summary()
        logger.info(
            "Default RSS catalog ensured globally (%d channels, %d outlets, %d new rows inserted)",
            summary["total_channels"],
            summary["total_media_outlets"],
            inserted_total,
        )
    except Exception:
        logger.exception("Failed to seed RSS sources")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()

    _seed_admin_user()
    _seed_rss_sources()

    scheduler = CrawlerScheduler(
        db_factory=session_newsradar,
        cron_expression=get_crawler_cron_expression(),
        run_on_startup=True,
    )
    app.state.crawler_scheduler = scheduler
    scheduler.start()

    yield

    await scheduler.stop()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url, "http://localhost:3000", "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    return app


app = create_app()
