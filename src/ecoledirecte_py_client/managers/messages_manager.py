from typing import TYPE_CHECKING, List, Literal
from .base_manager import BaseManager
from ..models.messages import Message, MessagesResponse

if TYPE_CHECKING:
    from ..client import Client


class MessagesManager(BaseManager):
    """Manager for handling student messages.

    This manager provides access to messages (received and sent) through the
    EcoleDirecte API and returns typed Pydantic models for easy manipulation.
    """

    def __init__(self, client: "Client"):
        """Initialize the MessagesManager.

        Args:
            client: The authenticated EcoleDirecte client instance.
        """
        super().__init__(client)

    async def list(
        self,
        student_id: int,
        message_type: Literal["received", "sent", "all"] = "received",
        sort_by_date: bool = True,
        unread_only: bool = False,
    ) -> List[Message]:
        """Retrieve messages for a student.

        Fetches messages from the API and returns a list of Message objects.
        By default, returns received messages sorted by date (most recent first).

        Args:
            student_id: The ID of the student whose messages to retrieve.
            message_type: Type of messages to retrieve. Options are:
                - "received": Only received messages (default)
                - "sent": Only sent messages
                - "all": Both received and sent messages
            sort_by_date: If True, sorts messages by date in descending order
                (most recent first). Defaults to True.
            unread_only: If True, only returns unread messages. Only applies to
                received messages. Defaults to False.

        Returns:
            A list of Message objects. Returns an empty list if no messages
            are found.

        Example:
            >>> # Get all received messages (sorted by date)
            >>> messages = await sdk.messages.list(student_id=12345)
            >>>
            >>> # Get unread messages only
            >>> unread = await sdk.messages.list(
            ...     student_id=12345,
            ...     unread_only=True
            ... )
            >>>
            >>> # Get sent messages
            >>> sent = await sdk.messages.list(
            ...     student_id=12345,
            ...     message_type="sent"
            ... )
            >>>
            >>> # Get all messages (received and sent)
            >>> all_messages = await sdk.messages.list(
            ...     student_id=12345,
            ...     message_type="all"
            ... )
        """
        # Note: The API endpoint URL structure from the original implementation
        # This endpoint returns both received and sent in the response
        url = (
            f"https://api.ecoledirecte.com/v3/eleves/{student_id}/messages.awp?"
            f"verbe=getall&typeRecuperation=received&orderBy=date&order=desc"
            f"&page=0&itemsPerPage=20&onlyRead=&query=&idClasseur=0"
        )
        response = await self.client.request(url)
        data = response.get("data", {})

        # Parse the response using the MessagesResponse model
        messages_response = MessagesResponse.model_validate(data)

        # Extract messages based on type
        messages: List[Message] = []
        if message_type == "received":
            messages = messages_response.received_messages
        elif message_type == "sent":
            messages = messages_response.sent_messages
        elif message_type == "all":
            messages = (
                messages_response.received_messages + messages_response.sent_messages
            )

        # Apply filters
        if unread_only and message_type in ("received", "all"):
            messages = [msg for msg in messages if not msg.read]

        # Apply sorting (descending by default - most recent first)
        if sort_by_date:
            messages.sort(key=lambda msg: msg.date, reverse=True)

        return messages
