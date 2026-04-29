from app.core.iptc import IPTC_CATEGORY_CODES
from app.core.seed_sources import get_seed_catalog_summary, seed_default_sources
from app.modules.sources.models import Category, InformationSource, RSSChannel


def test_default_catalog_summary_meets_source_checklist():
    summary = get_seed_catalog_summary()

    assert summary["total_channels"] >= 100
    assert summary["total_media_outlets"] >= 10
    assert summary["iptc_categories_covered"] == len(IPTC_CATEGORY_CODES)
    assert summary["covers_all_iptc_categories"] is True


def test_seed_populates_split_tables(db):
    """Tras T6.3, el seed crea Category, InformationSource y RSSChannel.

    El seed es idempotente: ``inserted`` puede ser 0 si otro test previo de la
    misma sesión ya pobló las tablas. Lo que verificamos es el estado final.
    """
    seed_default_sources(db)

    channels = db.query(RSSChannel).all()
    assert len(channels) >= 100

    media = db.query(InformationSource).all()
    assert len(media) >= 10

    covered_codes = {
        cat.name
        for cat in db.query(Category)
        .join(RSSChannel, RSSChannel.category_id == Category.id)
        .all()
    }
    assert set(IPTC_CATEGORY_CODES).issubset(covered_codes)
