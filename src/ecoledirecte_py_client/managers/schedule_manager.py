from typing import TYPE_CHECKING, List
from .base_manager import BaseManager
from ..models.schedule import ScheduleEvent, ScheduleResponse

if TYPE_CHECKING:
    from ..client import Client


class ScheduleManager(BaseManager):
    """Manager for handling student schedule and timetable.

    This manager provides access to schedule data through the EcoleDirecte API
    and returns typed Pydantic models for easy manipulation.
    """

    def __init__(self, client: "Client"):
        """Initialize the ScheduleManager.

        Args:
            client: The authenticated EcoleDirecte client instance.
        """
        super().__init__(client)

    async def list(
        self,
        student_id: int,
        start_date: str,
        end_date: str,
        sort_by_date: bool = True,
    ) -> List[ScheduleEvent]:
        """Retrieve schedule events for a student within a date range.

        Fetches schedule/timetable data from the API for the specified date range
        and returns a list of all events. By default, events are sorted by start date.

        Args:
            student_id: The ID of the student whose schedule to retrieve.
            start_date: Start date in ISO format (YYYY-MM-DD).
            end_date: End date in ISO format (YYYY-MM-DD).
            sort_by_date: If True, sorts events by start_date in ascending order.
                Defaults to True (logical for a schedule).

        Returns:
            A list of ScheduleEvent objects. Returns an empty list if no
            events are found for the date range.

        Example:
            >>> # Get schedule for a specific week
            >>> events = await sdk.schedule.list(
            ...     student_id=12345,
            ...     start_date="2026-01-13",
            ...     end_date="2026-01-17"
            ... )
            >>>
            >>> # Get unsorted events (preserving API order)
            >>> events = await sdk.schedule.list(
            ...     student_id=12345,
            ...     start_date="2026-01-13",
            ...     end_date="2026-01-17",
            ...     sort_by_date=False
            ... )
        """
        url = f"https://api.ecoledirecte.com/v3/E/{student_id}/emploidutemps.awp?verbe=get&"
        payload = {"dateDebut": start_date, "dateFin": end_date}
        response = await self.client.request(url, payload)
        data = response.get("data", [])

        # Parse the response using the ScheduleResponse model
        schedule_response = ScheduleResponse.model_validate(data)

        events = schedule_response.events

        # Apply sorting (enabled by default for schedules)
        if sort_by_date:
            events.sort(key=lambda event: event.start_date)

        return events
