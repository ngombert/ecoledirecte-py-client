"""
Tests for messages models (messages.py).
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from ecoledirecte_py_client.models.messages import (
    Message,
    MessageFile,
    MessagesResponse,
)


class TestMessage:
    """Tests for the Message model."""

    def test_message_parsing(self):
        """Test parsing a message."""
        data = {
            "id": 12345,
            "responseId": 0,
            "forwardId": 0,
            "mtype": "received",
            "read": False,
            "idDossier": 0,
            "idClasseur": 0,
            "transferred": False,
            "answered": False,
            "to_cc_cci": "",
            "brouillon": False,
            "canAnswer": True,
            "subject": "Important Notice",
            "content": "Please review the homework for tomorrow.",
            "date": "2024-01-15 10:30:00",
            "to": [],
            "from": {
                "id": 1,
                "prenom": "Teacher",
                "nom": "Name",
                "role": "P",
                "civilite": "M.",
            },
            "files": [],
        }

        message = Message.model_validate(data)

        assert message.id == 12345
        assert message.subject == "Important Notice"
        assert message.read is False
        assert message.from_sender.nom == "Name"

    def test_message_date_parsing(self):
        """Test that date string is parsed to datetime."""
        data = {
            "id": 1,
            "responseId": 0,
            "forwardId": 0,
            "mtype": "received",
            "read": False,
            "idDossier": 0,
            "idClasseur": 0,
            "transferred": False,
            "answered": False,
            "to_cc_cci": "",
            "brouillon": False,
            "canAnswer": True,
            "subject": "Test",
            "content": "Content",
            "date": "2024-01-15 10:30:00",
            "from": {
                "id": 1,
                "prenom": "Teacher",
                "nom": "Name",
                "role": "P",
            },
        }

        message = Message.model_validate(data)

        assert isinstance(message.date, datetime)
        assert message.date.year == 2024
        assert message.date.month == 1

    def test_message_read_status(self):
        """Test message read/unread status."""
        base_data = {
            "responseId": 0,
            "forwardId": 0,
            "mtype": "received",
            "idDossier": 0,
            "idClasseur": 0,
            "transferred": False,
            "answered": False,
            "to_cc_cci": "",
            "brouillon": False,
            "canAnswer": True,
            "content": "Content",
            "from": {
                "id": 1,
                "prenom": "Teacher",
                "nom": "Name",
                "role": "P",
            },
        }
        read_msg = Message.model_validate(
            {
                **base_data,
                "id": 1,
                "subject": "Read",
                "date": "2024-01-15 10:00:00",
                "read": True,
            }
        )
        unread_msg = Message.model_validate(
            {
                **base_data,
                "id": 2,
                "subject": "Unread",
                "date": "2024-01-15 10:00:00",
                "read": False,
            }
        )

        assert read_msg.read is True
        assert unread_msg.read is False

    def test_message_with_attachments(self):
        """Test message with file attachments."""
        data = {
            "id": 1,
            "responseId": 0,
            "forwardId": 0,
            "mtype": "received",
            "read": False,
            "idDossier": 0,
            "idClasseur": 0,
            "transferred": False,
            "answered": False,
            "to_cc_cci": "",
            "brouillon": False,
            "canAnswer": True,
            "subject": "With Files",
            "content": "Content",
            "date": "2024-01-15 10:00:00",
            "from": {
                "id": 1,
                "prenom": "Teacher",
                "nom": "Name",
                "role": "P",
            },
            "files": [
                {
                    "id": 100,
                    "libelle": "document.pdf",
                    "type": "pdf",
                    "date": "2024-01-15",
                    "etatSignatures": [],
                    "signature": {},
                }
            ],
        }

        message = Message.model_validate(data)

        # Check if model handles files field
        assert len(message.files) == 1
        assert message.files[0].libelle == "document.pdf"


class TestMessageFile:
    """Tests for the MessageFile model."""

    def test_message_file_parsing(self):
        """Test parsing a message file attachment."""
        data = {
            "id": 100,
            "libelle": "homework.pdf",
            "type": "pdf",
            "date": "2024-01-15",
            "etatSignatures": [],
            "signature": {},
        }

        file = MessageFile.model_validate(data)

        assert file.id == 100
        assert file.libelle == "homework.pdf"


class TestMessagesResponse:
    """Tests for the MessagesResponse model."""

    def test_messages_response_parsing(self):
        """Test parsing messages response."""
        msg_base = {
            "responseId": 0,
            "forwardId": 0,
            "mtype": "received",
            "idDossier": 0,
            "idClasseur": 0,
            "transferred": False,
            "answered": False,
            "to_cc_cci": "",
            "brouillon": False,
            "canAnswer": True,
            "content": "Content",
            "from": {
                "id": 1,
                "prenom": "Teacher",
                "nom": "Name",
                "role": "P",
            },
        }

        data = {
            "messages": {
                "received": [
                    {
                        **msg_base,
                        "id": 1,
                        "subject": "Message 1",
                        "date": "2024-01-15 10:00:00",
                        "read": False,
                    },
                    {
                        **msg_base,
                        "id": 2,
                        "subject": "Message 2",
                        "date": "2024-01-14 15:30:00",
                        "read": True,
                    },
                ],
                "sent": [
                    {
                        **msg_base,
                        "id": 3,
                        "subject": "Sent Message",
                        "date": "2024-01-13 09:00:00",
                        "read": True,
                        "mtype": "sent",
                    }
                ],
            },
            "classeurs": [],
        }

        response = MessagesResponse.model_validate(data)

        # Verify response structure based on actual model
        assert len(response.received_messages) == 2
        assert len(response.sent_messages) == 1
        assert response.unread_count == 1

    def test_messages_response_empty(self):
        """Test empty messages response."""
        data = {"messages": {"received": [], "sent": []}, "classeurs": []}

        response = MessagesResponse.model_validate(data)

        assert response is not None
        assert len(response.received_messages) == 0
