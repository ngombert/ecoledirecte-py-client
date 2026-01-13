"""
Tests for schedule models (schedule.py).
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from ecoledirecte_py_client.models.schedule import ScheduleEvent, ScheduleResponse
from tests.test_helpers import create_mock_schedule_event


class TestScheduleEvent:
    """Tests for the ScheduleEvent model."""

    def test_schedule_event_parsing(self):
        """Test parsing a schedule event."""
        data = create_mock_schedule_event(
            subject="Mathématiques",
            start="2024-01-15 08:00:00",
            end="2024-01-15 09:00:00",
            room="A101",
        )

        event = ScheduleEvent.model_validate(data)

        assert event.text == "Mathématiques"
        assert event.salle == "A101"

    def test_schedule_event_datetime_parsing(self):
        """Test that datetime strings are parsed correctly."""
        data = create_mock_schedule_event(
            start="2024-01-15 08:00:00", end="2024-01-15 09:00:00"
        )

        event = ScheduleEvent.model_validate(data)

        assert isinstance(event.start_date, datetime)
        assert isinstance(event.end_date, datetime)
        assert event.start_date.hour == 8
        assert event.end_date.hour == 9

    def test_schedule_event_type(self):
        """Test schedule event types."""
        cours = ScheduleEvent.model_validate(
            create_mock_schedule_event(typeCours="COURS")
        )
        controle = ScheduleEvent.model_validate(
            create_mock_schedule_event(typeCours="CONTROLE")
        )

        assert cours.type_cours == "COURS"
        assert controle.type_cours == "CONTROLE"

    def test_schedule_event_with_minimal_fields(self):
        """Test schedule event with minimal required fields."""
        data = create_mock_schedule_event(
            subject="Math",
            start="2024-01-15 08:00:00",
            end="2024-01-15 09:00:00",
        )

        event = ScheduleEvent.model_validate(data)

        assert event.text == "Math"


class TestScheduleResponse:
    """Tests for the ScheduleResponse model."""

    def test_schedule_response_parsing(self):
        """Test parsing schedule response with multiple events."""
        data = [
            create_mock_schedule_event(
                subject="Math", start="2024-01-15 08:00:00", end="2024-01-15 09:00:00"
            ),
            create_mock_schedule_event(
                subject="French", start="2024-01-15 09:00:00", end="2024-01-15 10:00:00"
            ),
        ]

        # ScheduleResponse wraps list of events
        # The validator handles raw list
        response = ScheduleResponse.model_validate(data)

        assert len(response.events) == 2
        assert response.events[0].text == "Math"
        assert response.events[1].text == "French"

    def test_schedule_response_empty(self):
        """Test empty schedule response."""
        data = []

        response = ScheduleResponse.model_validate(data)

        assert response.events == []
