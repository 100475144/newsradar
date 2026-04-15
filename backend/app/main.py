import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.database import session_newsradar
from app.core.logging_config import configure_logging
from app.core.security import get_password_hash
from app.modules.auth.models import User
from app.modules.crawler.scheduler import (
    CrawlerScheduler,
    get_crawler_interval_seconds,
)

logger = logging.getLogger(__name__)


def _seed_admin_user() -> None:
    """Create the initial admin user if it does not exist yet."""
    db = session_newsradar()
    try:
        existing = db.query(User).filter(User.email == settings.admin_email).first()
        if existing:
            return

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
        db.add(admin)
        db.commit()
        logger.info("Admin user seeded: %s", settings.admin_email)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()

    _seed_admin_user()

    scheduler = CrawlerScheduler(
        db_factory=session_newsradar,
        interval_seconds=get_crawler_interval_seconds(),
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