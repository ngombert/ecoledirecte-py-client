from typing import TYPE_CHECKING, Optional, List, Dict, Any

if TYPE_CHECKING:
    from .client import Client


class Student:
    def __init__(self, session: "Client", account_id: int):
        self.session = session
        self.id = account_id

    async def get_grades(self, quarter: Optional[int] = None) -> Dict[str, Any]:
        """
        Retrieves the student's grades.
        Delegates to self.session.grades.get
        """
        return await self.session.grades.get(self.id, quarter)

    async def get_homework(self, sort_by_due_date: bool = False) -> List[Any]:
        """
        Retrieves homeworks.
        Delegates to self.session.homework.list

        Args:
            sort_by_due_date: If True, sorts assignments by due date.

        Returns:
            List of HomeworkAssignment objects.
        """
        return await self.session.homework.list(
            self.id, sort_by_due_date=sort_by_due_date
        )

    async def get_schedule(
        self, start_date: str, end_date: str, sort_by_date: bool = True
    ) -> List[Any]:
        """
        Retrieves schedule.
        Delegates to self.session.schedule.list

        Args:
            start_date: Start date in ISO format (YYYY-MM-DD).
            end_date: End date in ISO format (YYYY-MM-DD).
            sort_by_date: If True, sorts events by start date.

        Returns:
            List of ScheduleEvent objects.
        """
        return await self.session.schedule.list(
            self.id, start_date, end_date, sort_by_date=sort_by_date
        )

    async def get_messages(self, message_type: str = "received") -> List[Any]:
        """
        Retrieves messages.
        Delegates to self.session.messages.list

        Args:
            message_type: Type of messages ('received', 'sent', or 'all').

        Returns:
            List of Message objects.
        """
        return await self.session.messages.list(self.id, message_type=message_type)
