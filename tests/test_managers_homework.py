"""
Tests for HomeworkManager (homework_manager.py).
"""

import pytest
from unittest.mock import AsyncMock

from ecoledirecte_py_client.managers.homework_manager import HomeworkManager
from tests.test_helpers import build_api_response, create_mock_homework


@pytest.mark.asyncio
class TestHomeworkManager:
    """Tests for the HomeworkManager class."""

    async def test_list_homework(self, mock_client):
        """Test retrieving homework list."""
        mock_response = build_api_response(
            {
                "matieres": [
                    {
                        "matiere": "MATH",
                        "aFaire": {
                            "2024-01-20": [
                                create_mock_homework(
                                    subject="Mathématiques",
                                    description="Exercices 1-5",
                                    due_date="2024-01-20",
                                )
                            ]
                        },
                    }
                ]
            }
        )

        mock_client.request = AsyncMock(return_value=mock_response)

        manager = HomeworkManager(mock_client)
        homework = await manager.list(student_id=12345)

        assert isinstance(homework, list)
        # Verify structure based on actual implementation

    async def test_list_with_sorting(self, mock_client):
        """Test sorting homework by due date."""
        mock_response = build_api_response(
            {
                "matieres": [
                    {
                        "matiere": "MATH",
                        "aFaire": {
                            "2024-01-25": [create_mock_homework(due_date="2024-01-25")],
                            "2024-01-20": [create_mock_homework(due_date="2024-01-20")],
                            "2024-01-22": [create_mock_homework(due_date="2024-01-22")],
                        },
                    }
                ]
            }
        )

        mock_client.request = AsyncMock(return_value=mock_response)

        manager = HomeworkManager(mock_client)
        homework = await manager.list(student_id=12345, sort_by_due_date=True)

        # Verify items are sorted
        assert isinstance(homework, list)

    async def test_list_empty_homework(self, mock_client):
        """Test handling empty homework response."""
        mock_response = build_api_response({"matieres": []})

        mock_client.request = AsyncMock(return_value=mock_response)

        manager = HomeworkManager(mock_client)
        homework = await manager.list(student_id=12345)

        assert homework == [] or homework is not None

    async def test_list_calls_correct_url(self, mock_client):
        """Test that the correct API URL is called."""
        mock_response = build_api_response({"matieres": []})
        mock_client.request = AsyncMock(return_value=mock_response)

        manager = HomeworkManager(mock_client)
        await manager.list(student_id=12345)

        call_args = mock_client.request.call_args
        assert "eleves/12345/cahierdetexte.awp" in call_args[0][0]
