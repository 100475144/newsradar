import pytest

@pytest.fixture
def stats_payload():
    return {
        "metrics": [
            {"name": "Total Users", "value": 10},
            {"name": "Total News", "value": 50},
        ]
    }

@pytest.fixture
def invalid_stats_payload():
    return {
        "metrics": []
    }
