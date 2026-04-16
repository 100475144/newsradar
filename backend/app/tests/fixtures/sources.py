import pytest

@pytest.fixture
def sample_source():
    return {
        "name": "Test Source",
        "url": "https://example.com/rss"
    }