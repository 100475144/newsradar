"""Test alert priority field functionality."""

import pytest
from app.modules.alerts.schemas import AlertCreateInternal, AlertResponse, AlertUpdate


def test_alert_priority_validation():
    """Test that priority field validates correctly (1-3 range)."""
    # Valid priorities
    for priority in [1, 2, 3]:
        data = AlertCreateInternal(
            name="test",
            descriptors=["test"],
            categories=[],
            priority=priority,
        )
        assert data.priority == priority

    # Invalid priorities (outside 1-3 range)
    with pytest.raises(ValueError):
        AlertCreateInternal(
            name="test",
            descriptors=["test"],
            categories=[],
            priority=0,
        )

    with pytest.raises(ValueError):
        AlertCreateInternal(
            name="test",
            descriptors=["test"],
            categories=[],
            priority=4,
        )


def test_alert_priority_default():
    """Test that priority defaults to 2 (medium)."""
    data = AlertCreateInternal(
        name="test",
        descriptors=["test"],
        categories=[],
    )
    assert data.priority == 2


def test_alert_response_priority():
    """Test that AlertResponse includes priority field."""
    response_data = {
        "id": 1,
        "user_id": 1,
        "name": "test",
        "descriptors": ["test"],
        "categories": [],
        "rss_channels_ids": [],
        "information_sources_ids": [],
        "cron_expression": "* * * * *",
        "priority": 1,
        "notify_in_app": True,
        "notify_email": False,
        "is_active": True,
    }
    response = AlertResponse(**response_data)
    assert response.priority == 1


def test_alert_update_priority():
    """Test that AlertUpdate allows partial priority updates."""
    data = AlertUpdate(priority=3)
    assert data.priority == 3

    data_no_priority = AlertUpdate(name="updated")
    assert data_no_priority.priority is None
