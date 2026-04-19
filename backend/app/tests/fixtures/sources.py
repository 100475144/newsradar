import pytest

@pytest.fixture
def sample_source():
    return {
        "medium_name": "Example News",
        "name": "Test Source",
        "url": "https://example.com/rss",
        "category": "science_technology",
    }
