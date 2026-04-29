from types import SimpleNamespace

from app.modules.alerts.matching import _resolve_news_classification
from app.modules.crawler.service import CrawlerService


def test_source_category_is_preferred_over_rss_when_available():
    category, origin = CrawlerService._resolve_initial_classification(
        item_category="technology",
        source_category="science_technology",
    )

    assert category == "science_technology"
    assert origin == "source"


def test_rss_category_is_used_when_source_has_no_category():
    category, origin = CrawlerService._resolve_initial_classification(
        item_category="technology",
        source_category=None,
    )

    assert category == "technology"
    assert origin == "rss"


def test_alert_classification_overrides_existing_news_category():
    # Tras T6.4, ``Alert.categories`` es una lista de objetos {code, label}.
    matching_alerts = [
        SimpleNamespace(
            id=8,
            categories=[{"code": "science_technology", "label": "Science"}],
        ),
        SimpleNamespace(
            id=3,
            categories=[{"code": "science_technology", "label": "Science"}],
        ),
        SimpleNamespace(
            id=9,
            categories=[{"code": "economy_business_finance", "label": "Economy"}],
        ),
    ]

    category, origin = _resolve_news_classification(
        current_category="economy_business_finance",
        current_origin="source",
        matching_alerts=matching_alerts,
    )

    assert category == "science_technology"
    assert origin == "alert"


def test_existing_classification_is_kept_when_no_alert_matches():
    category, origin = _resolve_news_classification(
        current_category="health",
        current_origin="source",
        matching_alerts=[],
    )

    assert category == "health"
    assert origin == "source"
