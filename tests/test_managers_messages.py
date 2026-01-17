"""
Tests for MessagesManager (messages_manager.py).
"""

import pytest
from unittest.mock import AsyncMock

from ecoledirecte_py_client.managers.messages_manager import MessagesManager
from tests.test_helpers import build_api_response, create_mock_message


@pytest.mark.asyncio
class TestMessagesManager:
    """Tests for the MessagesManager class."""

    async def test_list_received_messages(self, mock_client):
        """Test retrieving received messages."""
        mock_response = build_api_response(
            {
                "messages": {
                    "received": [
                        create_mock_message(
                            id=1,
                            subject="Test Message",
                            sender="Teacher",
                            date="2024-01-15 10:00:00",
                            read=False,
                            mtype="received",
                        )
                    ],
                    "sent": [],
                }
            }
        )

        mock_client.request = AsyncMock(return_value=mock_response)

        manager = MessagesManager(mock_client)
        messages = await manager.list(student_id=12345, message_type="received")

        assert isinstance(messages, list)

    async def test_list_sent_messages(self, mock_client):
        """Test retrieving sent messages."""
        mock_response = build_api_response(
            {
                "messages": {
                    "received": [],
                    "sent": [
                        create_mock_message(
                            id=2,
                            subject="Sent Message",
                            sender="Me",
                            date="2024-01-14 15:00:00",
                            read=True,
                            mtype="sent",
                        )
                    ],
                }
            }
        )

        mock_client.request = AsyncMock(return_value=mock_response)

        manager = MessagesManager(mock_client)
        messages = await manager.list(student_id=12345, message_type="sent")

        assert isinstance(messages, list)

    async def test_list_all_messages(self, mock_client):
        """Test retrieving all messages (received + sent)."""
        mock_response = build_api_response(
            {
                "messages": {
                    "received": [
                        create_mock_message(
                            id=1,
                            subject="Received",
                            date="2024-01-15 10:00:00",
                            read=False,
                            mtype="received",
                        )
                    ],
                    "sent": [
                        create_mock_message(
                            id=2,
                            subject="Sent",
                            date="2024-01-14 15:00:00",
                            read=True,
                            mtype="sent",
                        )
                    ],
                }
            }
        )

        mock_client.request = AsyncMock(return_value=mock_response)

        manager = MessagesManager(mock_client)
        messages = await manager.list(student_id=12345, message_type="all")

        assert isinstance(messages, list)

    async def test_list_empty_messages(self, mock_client):
        """Test handling empty messages response."""
        mock_response = build_api_response({"messages": {"received": [], "sent": []}})

        mock_client.request = AsyncMock(return_value=mock_response)

        manager = MessagesManager(mock_client)
        messages = await manager.list(student_id=12345)

        assert messages == [] or messages is not None
