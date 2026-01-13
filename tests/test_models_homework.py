"""
Tests for homework models (homework.py).
"""

import pytest
from datetime import datetime, date
from pydantic import ValidationError

from ecoledirecte_py_client.models.homework import HomeworkAssignment, HomeworkResponse
from tests.test_helpers import create_mock_homework


class TestHomeworkAssignment:
    """Tests for the HomeworkAssignment model."""

    def test_homework_parsing(self):
        """Test parsing a homework assignment."""
        data = create_mock_homework(
            subject="Mathématiques",
            description="Exercices 1 à 5 page 42",
            due_date="2024-01-20",
            given_date="2024-01-15",
            done=False,
        )

        homework = HomeworkAssignment.model_validate(data)

        assert homework.matiere == "Mathématiques"
        # a_faire is bool in model
        assert homework.a_faire is True
        assert homework.effectue is False

    def test_homework_date_parsing(self):
        """Test that date strings are parsed to datetime."""
        data = create_mock_homework(due_date="2024-01-20", given_date="2024-01-15")

        # Note: These might be in homework response, not directly in assignment
        homework = HomeworkAssignment.model_validate(data)

        assert homework.donne_le == date(2024, 1, 15)

    def test_homework_done_status(self):
        """Test homework completion status."""
        done_hw = HomeworkAssignment.model_validate(create_mock_homework(done=True))
        not_done_hw = HomeworkAssignment.model_validate(
            create_mock_homework(done=False)
        )

        assert done_hw.effectue is True
        assert not_done_hw.effectue is False

    def test_homework_with_optional_fields(self):
        """Test homework with minimal required fields."""
        data = create_mock_homework(subject="English", description="Read chapter 3")

        homework = HomeworkAssignment.model_validate(data)

        assert homework.a_faire is True
        assert homework.matiere == "English"


class TestHomeworkResponse:
    """Tests for the HomeworkResponse model."""

    def test_homework_response_parsing(self):
        """Test parsing homework response with subjects."""
        # Note: HomeworkResponse parses dict {date: [assignments]} and wraps in 'days' via/validator
        # But if we pass "days" directly, it should work too?
        # The validator says: if isinstance(data, dict) and "days" not in data: wrap it.
        # So typically we pass raw dict.

        raw_data = {
            "2024-01-20": [create_mock_homework(subject="Math", due_date="2024-01-20")],
            "2024-01-21": [
                create_mock_homework(subject="French", due_date="2024-01-21")
            ],
        }

        response = HomeworkResponse.model_validate(raw_data)

        # The response structure depends on the actual model
        # This test validates the response can be parsed
        assert response is not None
        assert response.total_assignments == 2

    def test_homework_response_empty(self):
        """Test empty homework response."""
        data = {}

        response = HomeworkResponse.model_validate(data)

        assert response is not None
        assert response.total_assignments == 0
