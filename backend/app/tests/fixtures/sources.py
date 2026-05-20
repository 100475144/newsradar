import pytest
from app.modules.sources.api import _check_url_resolvable, _check_rss_content

@pytest.fixture
def sample_source():
    return {
        "medium_name": "Example News",
        "name": "Test Source",
        "url": "https://example.com/rss",
        "category": "science_technology",
    }

@pytest.fixture
def bypass_url_validation(monkeypatch):

    def fake_url_check(url: str, timeout: float = 2.0):
        return None

    monkeypatch.setattr(
        "app.modules.sources.api._check_url_resolvable",
        fake_url_check,
    )

@pytest.fixture
def bypass_rss_content_validation(monkeypatch):

    def fake_rss_content_check(url: str, timeout: float = 2.0):
        return None

    monkeypatch.setattr(
        "app.modules.sources.api._check_rss_content",
        fake_rss_content_check,
    )