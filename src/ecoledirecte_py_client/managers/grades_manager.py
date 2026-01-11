from typing import TYPE_CHECKING, Optional, Dict, Any
from .base_manager import BaseManager

if TYPE_CHECKING:
    from ..client import Client


class GradesManager(BaseManager):
    """Manager for handling student grades."""

    def __init__(self, client: "Client"):
        super().__init__(client)

    async def get(
        self, student_id: int, quarter: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Retrieves the student's grades.

        Args:
            student_id: The ID of the student.
            quarter: (Optional) Specific quarter/period ID (e.g., 1 for A001).
                     If None, returns all grades.

        Returns:
            Dict containing grades data.
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
