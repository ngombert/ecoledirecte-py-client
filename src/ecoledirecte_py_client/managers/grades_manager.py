from typing import TYPE_CHECKING, List, Optional, Dict, Any
from .base_manager import BaseManager
from ..models.grades import Grade, GradesResponse

if TYPE_CHECKING:
    from ..client import Client


class GradesManager(BaseManager):
    """Manager for handling student grades.

    This manager provides access to grades data through the EcoleDirecte API
    and returns typed Pydantic models for easy manipulation.
    """

    def __init__(self, client: "Client"):
        """Initialize the GradesManager.

        Args:
            client: The authenticated EcoleDirecte client instance.
        """
        super().__init__(client)

    async def get(
        self, student_id: int, quarter: Optional[int] = None
    ) -> Dict[str, Any]:
        """Retrieve the student's grades (legacy method).

        This method maintains backward compatibility with the original implementation.
        For new code, consider using the `list()` method instead.

        Args:
            student_id: The ID of the student.
            quarter: Optional specific quarter/period ID (e.g., 1 for A001).
                If None, returns all grades.

        Returns:
            Dict containing grades data from the API response.
        """
        # Note: verbe=get is standard for their API
        url = (
            f"https://api.ecoledirecte.com/v3/eleves/{student_id}/notes.awp?verbe=get&"
        )
        response = await self.client.request(url)

        data = response.get("data", {})

        if quarter:
            period_id = f"A00{quarter}"
            periods = data.get("periodes", [])
            for p in periods:
                if p.get("idPeriode") == period_id:
                    return p
            return {}

        # Return the 'notes' array usually found at the top level for 'all'
        return data.get("notes", [])

    async def list(
        self,
        student_id: int,
        period_id: Optional[str] = None,
        sort_by_date: bool = False,
    ) -> List[Grade]:
        """Retrieve all grades for a student as typed Grade objects.

        Fetches grades from the API and returns a list of Grade objects.
        Optionally filters by period and sorts by date.

        Args:
            student_id: The ID of the student whose grades to retrieve.
            period_id: Optional period identifier (e.g., "A001" for first trimester).
                If None, returns grades from all periods.
            sort_by_date: If True, sorts grades by date in ascending order
                (oldest first). Defaults to False.

        Returns:
            A list of Grade objects. Returns an empty list if no grades are found.

        Example:
            >>> # Get all grades for a student
            >>> grades = await sdk.grades.list(student_id=12345)
            >>>
            >>> # Get grades for a specific period, sorted by date
            >>> q1_grades = await sdk.grades.list(
            ...     student_id=12345,
            ...     period_id="A001",
            ...     sort_by_date=True
            ... )
            >>>
            >>> # Calculate average
            >>> total = sum(g.value for g in grades if g.value is not None)
            >>> avg = total / len([g for g in grades if g.value is not None])
        """
        url = (
            f"https://api.ecoledirecte.com/v3/eleves/{student_id}/notes.awp?verbe=get&"
        )
        response = await self.client.request(url)
        data = response.get("data", {})

        # Parse using the GradesResponse model
        grades_response = GradesResponse.model_validate(data)

        # Collect all grades
        all_grades = grades_response.notes

        # Apply period filter if specified
        if period_id:
            all_grades = [
                grade for grade in all_grades if grade.code_periode == period_id
            ]

        # Apply sorting
        if sort_by_date:
            all_grades.sort(key=lambda g: g.date)

        return all_grades
