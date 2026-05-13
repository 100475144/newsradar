"""Default RSS catalog: 100+ canales en 14+ medios cubriendo las 17 categorías IPTC.

Adaptado al modelo split (T6.3): siembra ``InformationSource`` (medios) y
``RSSChannel`` (feeds) referenciando ``Category`` por id.
"""

from __future__ import annotations

from collections.abc import Iterable
from urllib.parse import urlsplit

from sqlalchemy.orm import Session

from app.core.iptc import IPTC_CATEGORIES, IPTC_CATEGORY_CODES, legacy_code_to_iptc
from app.modules.sources.models import Category, InformationSource, RSSChannel


# Cada tupla: ("Medium - Channel", rss_url, iptc_category_code)
RSS_SEEDS_RAW: list[tuple[str, str, str]] = [
    # BBC
    ("BBC - Top Stories", "https://feeds.bbci.co.uk/news/rss.xml", "society"),
    ("BBC - World", "https://feeds.bbci.co.uk/news/world/rss.xml", "conflict_war_peace"),
    ("BBC - Business", "https://feeds.bbci.co.uk/news/business/rss.xml", "economy_business_finance"),
    ("BBC - Politics", "https://feeds.bbci.co.uk/news/politics/rss.xml", "politics"),
    ("BBC - Health", "https://feeds.bbci.co.uk/news/health/rss.xml", "health"),
    ("BBC - Science & Environment", "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml", "science_technology"),
    ("BBC - Technology", "https://feeds.bbci.co.uk/news/technology/rss.xml", "science_technology"),
    ("BBC - Entertainment & Arts", "https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml", "arts_culture_entertainment"),
    ("BBC - Education", "https://feeds.bbci.co.uk/news/education/rss.xml", "education"),
    ("BBC - Sport", "https://feeds.bbci.co.uk/sport/rss.xml", "sport"),

    # Reuters
    ("Reuters - World", "https://www.reutersagency.com/feed/?best-topics=world&post_type=best", "conflict_war_peace"),
    ("Reuters - Business", "https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best", "economy_business_finance"),
    ("Reuters - Technology", "https://www.reutersagency.com/feed/?best-topics=tech&post_type=best", "science_technology"),
    ("Reuters - Sports", "https://www.reutersagency.com/feed/?best-topics=sports&post_type=best", "sport"),
    ("Reuters - Lifestyle", "https://www.reutersagency.com/feed/?best-topics=lifestyle&post_type=best", "lifestyle_leisure"),
    ("Reuters - Environment", "https://www.reutersagency.com/feed/?best-topics=environment&post_type=best", "environment"),

    # The Guardian
    ("The Guardian - World", "https://www.theguardian.com/world/rss", "conflict_war_peace"),
    ("The Guardian - Politics", "https://www.theguardian.com/politics/rss", "politics"),
    ("The Guardian - Environment", "https://www.theguardian.com/environment/rss", "environment"),
    ("The Guardian - Science", "https://www.theguardian.com/science/rss", "science_technology"),
    ("The Guardian - Technology", "https://www.theguardian.com/technology/rss", "science_technology"),
    ("The Guardian - Business", "https://www.theguardian.com/business/rss", "economy_business_finance"),
    ("The Guardian - Sport", "https://www.theguardian.com/sport/rss", "sport"),
    ("The Guardian - Culture", "https://www.theguardian.com/culture/rss", "arts_culture_entertainment"),
    ("The Guardian - Education", "https://www.theguardian.com/education/rss", "education"),
    ("The Guardian - Society", "https://www.theguardian.com/society/rss", "society"),
    ("The Guardian - Law", "https://www.theguardian.com/law/rss", "crime_law_justice"),
    ("The Guardian - Weather", "https://www.theguardian.com/weather/rss", "weather"),
    ("The Guardian - UK News", "https://www.theguardian.com/uk-news/rss", "society"),

    # El Pais
    ("El Pais - Portada", "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada", "society"),
    ("El Pais - Internacional", "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/internacional", "conflict_war_peace"),
    ("El Pais - Economia", "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/economia", "economy_business_finance"),
    ("El Pais - Ciencia", "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/ciencia", "science_technology"),
    ("El Pais - Tecnologia", "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/tecnologia", "science_technology"),
    ("El Pais - Cultura", "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/cultura", "arts_culture_entertainment"),
    ("El Pais - Deportes", "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/deportes", "sport"),
    ("El Pais - Salud", "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/salud", "health"),
    ("El Pais - Educacion", "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/educacion", "education"),
    ("El Pais - Clima", "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/clima-y-medio-ambiente", "environment"),

    # CNN
    ("CNN - Top Stories", "http://rss.cnn.com/rss/edition.rss", "society"),
    ("CNN - World", "http://rss.cnn.com/rss/edition_world.rss", "conflict_war_peace"),
    ("CNN - Business", "http://rss.cnn.com/rss/money_news_international.rss", "economy_business_finance"),
    ("CNN - Technology", "http://rss.cnn.com/rss/edition_technology.rss", "science_technology"),
    ("CNN - Entertainment", "http://rss.cnn.com/rss/edition_entertainment.rss", "arts_culture_entertainment"),
    ("CNN - Sport", "http://rss.cnn.com/rss/edition_sport.rss", "sport"),
    ("CNN - Health", "http://rss.cnn.com/rss/edition_health.rss", "health"),

    # Al Jazeera
    ("Al Jazeera - News", "https://www.aljazeera.com/xml/rss/all.xml", "conflict_war_peace"),

    # NPR
    ("NPR - News", "https://feeds.npr.org/1001/rss.xml", "society"),
    ("NPR - World", "https://feeds.npr.org/1004/rss.xml", "conflict_war_peace"),
    ("NPR - Politics", "https://feeds.npr.org/1014/rss.xml", "politics"),
    ("NPR - Business", "https://feeds.npr.org/1006/rss.xml", "economy_business_finance"),
    ("NPR - Science", "https://feeds.npr.org/1007/rss.xml", "science_technology"),
    ("NPR - Health", "https://feeds.npr.org/1128/rss.xml", "health"),
    ("NPR - Education", "https://feeds.npr.org/1013/rss.xml", "education"),
    ("NPR - Arts & Life", "https://feeds.npr.org/1008/rss.xml", "arts_culture_entertainment"),
    ("NPR - Religion", "https://feeds.npr.org/1122/rss.xml", "religion_belief"),

    # The New York Times
    ("NYT - World", "https://rss.nytimes.com/services/xml/rss/nyt/World.xml", "conflict_war_peace"),
    ("NYT - Politics", "https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml", "politics"),
    ("NYT - Business", "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml", "economy_business_finance"),
    ("NYT - Technology", "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml", "science_technology"),
    ("NYT - Science", "https://rss.nytimes.com/services/xml/rss/nyt/Science.xml", "science_technology"),
    ("NYT - Health", "https://rss.nytimes.com/services/xml/rss/nyt/Health.xml", "health"),
    ("NYT - Sports", "https://rss.nytimes.com/services/xml/rss/nyt/Sports.xml", "sport"),
    ("NYT - Arts", "https://rss.nytimes.com/services/xml/rss/nyt/Arts.xml", "arts_culture_entertainment"),
    ("NYT - Education", "https://rss.nytimes.com/services/xml/rss/nyt/Education.xml", "education"),
    ("NYT - Climate", "https://rss.nytimes.com/services/xml/rss/nyt/Climate.xml", "environment"),
    ("NYT - Obituaries", "https://rss.nytimes.com/services/xml/rss/nyt/Obituaries.xml", "human_interest"),

    # Deutsche Welle
    ("DW - Top Stories", "https://rss.dw.com/rdf/rss-en-top", "society"),
    ("DW - World", "https://rss.dw.com/rdf/rss-en-world", "conflict_war_peace"),
    ("DW - Business", "https://rss.dw.com/rdf/rss-en-bus", "economy_business_finance"),
    ("DW - Science", "https://rss.dw.com/rdf/rss-en-sci", "science_technology"),
    ("DW - Environment", "https://rss.dw.com/rdf/rss-en-env", "environment"),
    ("DW - Culture", "https://rss.dw.com/rdf/rss-en-cul", "arts_culture_entertainment"),
    ("DW - Sports", "https://rss.dw.com/rdf/rss-en-sports", "sport"),

    # France 24
    ("France 24 - World", "https://www.france24.com/en/rss", "conflict_war_peace"),
    ("France 24 - France", "https://www.france24.com/en/france/rss", "politics"),
    ("France 24 - Business", "https://www.france24.com/en/eco-tech/rss", "economy_business_finance"),
    ("France 24 - Culture", "https://www.france24.com/en/culture/rss", "arts_culture_entertainment"),
    ("France 24 - Sport", "https://www.france24.com/en/sport/rss", "sport"),

    # ABC Australia
    ("ABC AU - Top Stories", "https://www.abc.net.au/news/feed/2942460/rss.xml", "society"),
    ("ABC AU - World", "https://www.abc.net.au/news/feed/51120/rss.xml", "conflict_war_peace"),
    ("ABC AU - Business", "https://www.abc.net.au/news/feed/51892/rss.xml", "economy_business_finance"),
    ("ABC AU - Science", "https://www.abc.net.au/news/feed/2932508/rss.xml", "science_technology"),
    ("ABC AU - Health", "https://www.abc.net.au/news/feed/54986/rss.xml", "health"),
    ("ABC AU - Sport", "https://www.abc.net.au/news/feed/2942520/rss.xml", "sport"),
    ("ABC AU - Entertainment", "https://www.abc.net.au/news/feed/2942474/rss.xml", "arts_culture_entertainment"),
    ("ABC AU - Environment", "https://www.abc.net.au/news/feed/2942482/rss.xml", "environment"),

    # El Mundo
    ("El Mundo - Portada", "https://e00-elmundo.uecdn.es/elmundo/rss/portada.xml", "society"),
    ("El Mundo - Internacional", "https://e00-elmundo.uecdn.es/elmundo/rss/internacional.xml", "conflict_war_peace"),
    ("El Mundo - Economia", "https://e00-elmundo.uecdn.es/elmundo/rss/economia.xml", "economy_business_finance"),
    ("El Mundo - Deportes", "https://e00-elmundo.uecdn.es/elmundo/rss/deportes.xml", "sport"),
    ("El Mundo - Cultura", "https://e00-elmundo.uecdn.es/elmundo/rss/cultura.xml", "arts_culture_entertainment"),
    ("El Mundo - Ciencia", "https://e00-elmundo.uecdn.es/elmundo/rss/ciencia.xml", "science_technology"),
    ("El Mundo - Salud", "https://e00-elmundo.uecdn.es/elmundo/rss/salud.xml", "health"),

    # RTVE
    ("RTVE - Noticias", "https://www.rtve.es/rss/noticias.xml", "society"),
    ("RTVE - Deportes", "https://www.rtve.es/rss/deportes.xml", "sport"),

    # The Independent
    ("The Independent - News", "https://www.independent.co.uk/news/rss", "society"),
    ("The Independent - Sport", "https://www.independent.co.uk/sport/rss", "sport"),
    ("The Independent - Life", "https://www.independent.co.uk/life-style/rss", "lifestyle_leisure"),
    ("The Independent - Arts", "https://www.independent.co.uk/arts-entertainment/rss", "arts_culture_entertainment"),
    ("The Independent - Travel", "https://www.independent.co.uk/travel/rss", "lifestyle_leisure"),
    ("The Independent - Climate", "https://www.independent.co.uk/climate-change/rss", "environment"),

    # Cobertura extra de IPTC branches
    ("ILO - News", "https://www.ilo.org/resource/news/rss", "labour"),
    ("AccuWeather - Top Stories", "https://rss.accuweather.com/rss/liveweather_rss.asp?metric=1&locCode=EUR", "weather"),
    ("ReliefWeb - Disasters", "https://reliefweb.int/updates/rss.xml", "disaster_accident"),
    ("UN News - Human Rights", "https://news.un.org/feed/subscribe/en/news/topic/human-rights/feed/rss.xml", "human_interest"),
    ("UN News - Peace & Security", "https://news.un.org/feed/subscribe/en/news/topic/peace-and-security/feed/rss.xml", "conflict_war_peace"),
    ("UN News - Climate", "https://news.un.org/feed/subscribe/en/news/topic/climate-change/feed/rss.xml", "environment"),
    ("Religion News Service - Latest", "https://religionnews.com/feed/", "religion_belief"),
    ("Crime Reads - Latest", "https://crimereads.com/feed/", "crime_law_justice"),
]


def _split_seed_name(display_name: str) -> tuple[str, str]:
    if " - " in display_name:
        medium_name, channel_name = display_name.split(" - ", 1)
        return medium_name.strip(), channel_name.strip()
    return display_name.strip(), display_name.strip()


def _derive_medium_url(rss_url: str) -> str:
    """Derive a medium homepage URL from one of its feed URLs."""
    parts = urlsplit(rss_url)
    if not parts.scheme or not parts.netloc:
        return rss_url
    return f"{parts.scheme}://{parts.netloc}"


def get_seed_sources() -> list[dict[str, str]]:
    """Return the normalized default catalog with explicit medium and channel names."""
    normalized_sources: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    for display_name, url, category in RSS_SEEDS_RAW:
        normalized_url = url.strip()
        if normalized_url in seen_urls:
            continue

        medium_name, channel_name = _split_seed_name(display_name)
        normalized_sources.append(
            {
                "medium_name": medium_name,
                "name": channel_name,
                "url": normalized_url,
                "category": legacy_code_to_iptc(category.strip().lower()),
            }
        )
        seen_urls.add(normalized_url)

    return normalized_sources


def get_seed_catalog_summary() -> dict[str, int | bool]:
    seeds = get_seed_sources()
    covered_categories = {seed["category"] for seed in seeds}
    media_outlets = {seed["medium_name"] for seed in seeds}
    expected_categories = set(IPTC_CATEGORY_CODES)

    return {
        "total_channels": len(seeds),
        "total_media_outlets": len(media_outlets),
        "iptc_categories_covered": len(covered_categories),
        "iptc_categories_total": len(expected_categories),
        "covers_all_iptc_categories": covered_categories == expected_categories,
    }


def seed_default_sources(db: Session) -> int:
    """Garantiza que el catálogo global de RSS exista (idempotente).

    Crea/usa categorías IPTC, ``InformationSource`` por cada medio y
    ``RSSChannel`` por cada feed, evitando duplicados por URL.
    """
    # Remove legacy categories seeded by the initial migration with autoincrement
    # IDs and English code names (e.g. "arts_culture_entertainment" with id=1).
    # The proper IPTC categories have id=int(code) like 1000000.
    iptc_id_set = {int(c) for c in IPTC_CATEGORY_CODES}
    for legacy_cat in db.query(Category).all():
        if legacy_cat.id not in iptc_id_set:
            db.delete(legacy_cat)
    db.flush()

    # Cache de categorías por code
    categories_by_name = {
        cat.name: cat
        for cat in db.query(Category).all()
    }
    # Asegurar todas las IPTC primer nivel (id = int(code), name = Spanish label, source = "IPTC")
    for code in IPTC_CATEGORY_CODES:
        label = IPTC_CATEGORIES[code]
        if label not in categories_by_name:
            cat = Category(id=int(code), name=label, source="IPTC")
            db.add(cat)
            db.flush()
            categories_by_name[label] = cat
        # Also index by numeric code for seed lookup
        categories_by_name[code] = categories_by_name[label]

    # Cache de information sources por nombre
    media_by_name = {
        m.name: m
        for m in db.query(InformationSource).all()
    }

    existing_channel_urls = {
        row[0]
        for row in db.query(RSSChannel.url).all()
    }

    new_channels = 0
    for seed in get_seed_sources():
        if seed["url"] in existing_channel_urls:
            continue

        # Asegurar el medio
        medium = media_by_name.get(seed["medium_name"])
        if medium is None:
            medium = InformationSource(
                name=seed["medium_name"],
                url=_derive_medium_url(seed["url"]),
            )
            db.add(medium)
            db.flush()
            media_by_name[seed["medium_name"]] = medium

        # Categoría (lookup by IPTC code from seed)
        category = categories_by_name.get(seed["category"])
        if category is None:
            # Fallback: create with IPTC code as id
            cat_id = int(seed["category"]) if seed["category"].isdigit() else None
            cat_label = IPTC_CATEGORIES.get(seed["category"], seed["category"])
            category = Category(id=cat_id, name=cat_label, source="IPTC") if cat_id else Category(name=cat_label, source="IPTC")
            db.add(category)
            db.flush()
            categories_by_name[seed["category"]] = category

        channel = RSSChannel(
            url=seed["url"],
            information_source_id=medium.id,
            category_id=category.id,
            name=seed["name"],
            is_active=True,
        )
        db.add(channel)
        existing_channel_urls.add(seed["url"])
        new_channels += 1

    if new_channels:
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

    return new_channels


def iter_seed_mediums() -> Iterable[str]:
    return (seed["medium_name"] for seed in get_seed_sources())
