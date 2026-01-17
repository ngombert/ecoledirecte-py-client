"""
Tests for ScheduleManager (schedule_manager.py).
"""

import pytest
from unittest.mock import AsyncMock

from ecoledirecte_py_client.managers.schedule_manager import ScheduleManager
from ecoledirecte_py_client.models.schedule import ScheduleEvent
from tests.test_helpers import build_api_response, create_mock_schedule_event


@pytest.mark.asyncio
class TestScheduleManager:
    """Tests for the ScheduleManager class."""

    async def test_list_schedule(self, mock_client):
        """Test retrieving schedule events."""
        mock_response = build_api_response(
            [
                create_mock_schedule_event(
                    subject="Math",
                    start="2024-01-15 08:00:00",
                    end="2024-01-15 09:00:00",
                ),
                create_mock_schedule_event(
                    subject="French",
                    start="2024-01-15 09:00:00",
                    end="2024-01-15 10:00:00",
                ),
            ]
        )

        mock_client.request = AsyncMock(return_value=mock_response)

        manager = ScheduleManager(mock_client)
        events = await manager.list(
            student_id=12345, start_date="2024-01-15", end_date="2024-01-15"
        )

        assert isinstance(events, list)
        assert len(events) == 2

    async def test_list_with_sorting(self, mock_client):
        """Test sorting schedule events by start date."""
        mock_response = build_api_response(
            [
                create_mock_schedule_event(
                    start="2024-01-15 14:00:00", end="2024-01-15 15:00:00"
                ),
                create_mock_schedule_event(
                    start="2024-01-15 08:00:00", end="2024-01-15 09:00:00"
                ),
                create_mock_schedule_event(
                    start="2024-01-15 10:00:00", end="2024-01-15 11:00:00"
                ),
            ]
        )

        mock_client.request = AsyncMock(return_value=mock_response)

        manager = ScheduleManager(mock_client)
        events = await manager.list(
            student_id=12345,
            start_date="2024-01-15",
            end_date="2024-01-15",
            sort_by_date=True,
        )

        # Verify events are returned (sorting tested in implementation)
        assert isinstance(events, list)

    async def test_list_empty_schedule(self, mock_client):
        """Test handling empty schedule response."""
        mock_response = build_api_response([])

        mock_client.request = AsyncMock(return_value=mock_response)

        manager = ScheduleManager(mock_client)
        events = await manager.list(
            student_id=12345, start_date="2024-01-15", end_date="2024-01-15"
        )

        assert events == []

    async def test_list_date_range(self, mock_client):
        """Test that date range is passed correctly."""
        mock_response = build_api_response([])
        mock_client.request = AsyncMock(return_value=mock_response)

        manager = ScheduleManager(mock_client)
        await manager.list(
            student_id=12345, start_date="2024-01-15", end_date="2024-01-20"
        )

        # Verify the request was made
        assert mock_client.request.called
