"""
Tests for GradesManager (grades_manager.py).
"""

import pytest
from unittest.mock import AsyncMock

from ecoledirecte_py_client.managers.grades_manager import GradesManager
from ecoledirecte_py_client.models.grades import Grade
from tests.test_helpers import build_api_response, create_mock_grade


@pytest.mark.asyncio
class TestGradesManager:
    """Tests for the GradesManager class."""

    async def test_get_all_grades(self, mock_client):
        """Test retrieving all grades using the get() method."""
        # Mock the client request
        mock_response = build_api_response(
            {
                "notes": [
                    create_mock_grade(value="15", subject="Math"),
                    create_mock_grade(value="16", subject="French"),
                ],
                "periodes": [],
            }
        )

        mock_client.request = AsyncMock(return_value=mock_response)

        manager = GradesManager(mock_client)
        result = await manager.get(student_id=12345)

        assert isinstance(result, list)
        assert len(result) == 2

    async def test_get_grades_by_quarter(self, mock_client):
        """Test retrieving grades for a specific quarter."""
        mock_response = build_api_response(
            {
                "notes": [],
                "periodes": [
                    {
                        "idPeriode": "A001",
                        "periode": "1er Trimestre",
                        "ensavoirs": [],
                        "notes": [create_mock_grade(value="15", codePeriode="A001")],
                    }
                ],
            }
        )

        mock_client.request = AsyncMock(return_value=mock_response)

        manager = GradesManager(mock_client)
        result = await manager.get(student_id=12345, quarter=1)

        assert isinstance(result, dict)
        assert result.get("idPeriode") == "A001"

    async def test_list_returns_grade_objects(self, mock_client):
        """Test that list() returns typed Grade objects."""
        mock_response = build_api_response(
            {
                "notes": [
                    create_mock_grade(value="15", subject="Math", date="2024-01-15"),
                    create_mock_grade(value="16", subject="French", date="2024-01-16"),
                ],
                "periodes": [],
            }
        )

        mock_client.request = AsyncMock(return_value=mock_response)

        manager = GradesManager(mock_client)
        grades = await manager.list(student_id=12345)

        assert isinstance(grades, list)
        assert len(grades) == 2
        assert all(isinstance(g, Grade) for g in grades)
        assert grades[0].valeur == 15.0
        assert grades[1].valeur == 16.0

    async def test_list_with_period_filter(self, mock_client):
        """Test filtering grades by period."""
        mock_response = build_api_response(
            {
                "notes": [
                    create_mock_grade(value="15", codePeriode="A001"),
                    create_mock_grade(value="16", codePeriode="A002"),
                    create_mock_grade(value="17", codePeriode="A001"),
                ],
                "periodes": [],
            }
        )

        mock_client.request = AsyncMock(return_value=mock_response)

        manager = GradesManager(mock_client)
        grades = await manager.list(student_id=12345, period_id="A001")

        # Should only return grades from period A001
        assert len(grades) == 2
        assert all(g.code_periode == "A001" for g in grades)

    async def test_list_with_sorting(self, mock_client):
        """Test sorting grades by date."""
        mock_response = build_api_response(
            {
                "notes": [
                    create_mock_grade(value="15", date="2024-01-20"),
                    create_mock_grade(value="16", date="2024-01-10"),
                    create_mock_grade(value="17", date="2024-01-15"),
                ],
                "periodes": [],
            }
        )

        mock_client.request = AsyncMock(return_value=mock_response)

        manager = GradesManager(mock_client)
        grades = await manager.list(student_id=12345, sort_by_date=True)

        # Should be sorted in ascending order (oldest first)
        assert grades[0].date.day == 10
        assert grades[1].date.day == 15
        assert grades[2].date.day == 20

    async def test_list_handles_absent_grades(self, mock_client):
        """Test that list() handles non-numeric grades properly."""
        mock_response = build_api_response(
            {
                "notes": [
                    create_mock_grade(value="15"),
                    create_mock_grade(value="Abs"),
                    create_mock_grade(value="N.Not"),
                ],
                "periodes": [],
            }
        )

        mock_client.request = AsyncMock(return_value=mock_response)

        manager = GradesManager(mock_client)
        grades = await manager.list(student_id=12345)

        assert len(grades) == 3
        assert grades[0].valeur == 15.0
        assert grades[1].valeur is None  # Abs
        assert grades[2].valeur is None  # N.Not

    async def test_list_empty_response(self, mock_client):
        """Test handling empty grades response."""
        mock_response = build_api_response({"notes": [], "periodes": []})

        mock_client.request = AsyncMock(return_value=mock_response)

        manager = GradesManager(mock_client)
        grades = await manager.list(student_id=12345)

        assert grades == []

    async def test_get_calls_correct_url(self, mock_client):
        """Test that the correct API URL is called."""
        mock_response = build_api_response({"notes": [], "periodes": []})
        mock_client.request = AsyncMock(return_value=mock_response)

        manager = GradesManager(mock_client)
        await manager.get(student_id=12345)

        # Verify the URL was called correctly
        call_args = mock_client.request.call_args
        assert "eleves/12345/notes.awp" in call_args[0][0]
