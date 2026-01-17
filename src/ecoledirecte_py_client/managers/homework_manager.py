from typing import TYPE_CHECKING, List
from .base_manager import BaseManager
from ..models.homework import HomeworkAssignment, HomeworkResponse

if TYPE_CHECKING:
    from ..client import Client


class HomeworkManager(BaseManager):
    """Manager for handling student homework assignments.

    This manager provides access to homework data through the EcoleDirecte API
    and returns typed Pydantic models for easy manipulation.
    """

    def __init__(self, client: "Client"):
        """Initialize the HomeworkManager.

        Args:
            client: The authenticated EcoleDirecte client instance.
        """
        super().__init__(client)

    async def list(
        self,
        student_id: int,
        sort_by_due_date: bool = False,
        pending_only: bool = False,
    ) -> List[HomeworkAssignment]:
        """Retrieve all homework assignments for a student.

        Fetches homework data from the API and returns a flat list of all assignments
        across all dates. Optionally filters and sorts the results.

        Args:
            student_id: The ID of the student whose homework to retrieve.
            sort_by_due_date: If True, sorts assignments by due date (pour_le) in
                ascending order. Defaults to False.
            pending_only: If True, only returns assignments that are not yet completed
                (effectue=False). Defaults to False.

        Returns:
            A list of HomeworkAssignment objects. Returns an empty list if no
            homework is found.

        Example:
            >>> # Get all homework for a student
            >>> homework = await sdk.homework.list(student_id=12345)
            >>>
            >>> # Get pending homework sorted by due date
            >>> pending = await sdk.homework.list(
            ...     student_id=12345,
            ...     sort_by_due_date=True,
            ...     pending_only=True
            ... )
        """
        url = f"https://api.ecoledirecte.com/v3/eleves/{student_id}/cahierdetexte.awp?verbe=get&"
        response = await self.client.request(url)
        data = response.get("data", {})

        # Parse the response using the HomeworkResponse model
        homework_response = HomeworkResponse.model_validate(data)

        # Flatten all assignments from all days into a single list
        all_assignments: List[HomeworkAssignment] = []
        for assignments in homework_response.days.values():
            all_assignments.extend(assignments)

        # Apply filters
        if pending_only:
            all_assignments = [hw for hw in all_assignments if not hw.effectue]

        # Apply sorting
        if sort_by_due_date:
            all_assignments.sort(key=lambda hw: hw.pour_le)

        return all_assignments
