from app.core.iptc import IPTC_CATEGORY_CODES
from app.core.seed_sources import get_seed_catalog_summary
from app.modules.auth.repository import UserRepository
from app.modules.auth.schemas import UserCreate
from app.modules.auth.service import AuthService
from app.modules.sources.models import Source


def test_default_catalog_summary_meets_source_checklist():
    summary = get_seed_catalog_summary()

    assert summary["total_channels"] >= 100
    assert summary["total_media_outlets"] >= 10
    assert summary["iptc_categories_covered"] == len(IPTC_CATEGORY_CODES)
    assert summary["covers_all_iptc_categories"] is True


def test_register_user_receives_default_catalog(db, monkeypatch):
    # Este test ya no tiene tanto sentido ahora que las fuentes RSS 
    # son individuales por cada usuario
    # TODO: Hacer test verificando que las 110 fuentes se añaden 
    # al iniciar el sistema 
    monkeypatch.setattr(
        "app.modules.auth.service.send_verification_email",
        lambda *_args, **_kwargs: True,
    )

    auth_service = AuthService(UserRepository(db))
    user = auth_service.register_user(
        UserCreate(
            email="catalog-test@example.com",
            first_name="Catalog",
            last_name="Tester",
            organization="NewsRadar",
            password="Password123!",
        )
    )

    sources = db.query(Source).all()

    assert len(sources) >= 100
    assert len({source.medium_name for source in sources}) >= 10
    assert {source.category for source in sources if source.category}.issuperset(IPTC_CATEGORY_CODES)
