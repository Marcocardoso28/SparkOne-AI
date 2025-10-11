"""Shared fixtures for tests."""

import pytest
from datetime import datetime, UTC

from app.infrastructure.database.models.tasks import TaskRecord, TaskStatus
from app.infrastructure.database.models.user import User
from app.infrastructure.database.models.events import EventRecord, EventStatus


@pytest.fixture
def sample_task():
    """Create a sample task for testing."""
    return TaskRecord(
        id=1,
        title="Test Task",
        description="A test task description",
        status=TaskStatus.PENDING,
        priority="medium",
        due_date=datetime.now(UTC),
        channel="test",
        sender="test_user",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )


@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    return User(
        id=1,
        username="test_user",
        email="test@example.com",
        password_hash="hashed_password",
        is_active=True,
        is_verified=True,
        two_factor_enabled=False,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )


@pytest.fixture
def sample_event():
    """Create a sample event for testing."""
    return EventRecord(
        id=1,
        title="Test Event",
        description="A test event description",
        start_time=datetime.now(UTC),
        end_time=datetime.now(UTC),
        status=EventStatus.CONFIRMED,
        calendar_id="test_calendar",
        external_id="ext_123",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )


@pytest.fixture
def sample_channel_message():
    """Create a sample channel message for testing."""
    from app.models.schemas import ChannelMessage

    return ChannelMessage(
        channel="test",
        sender="test_user",
        content="Test message content",
        message_type="free_text",
        extra_data={}
    )
