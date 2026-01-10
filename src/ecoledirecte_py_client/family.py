from typing import TYPE_CHECKING, Any, Dict, List
from .student import Student

if TYPE_CHECKING:
    from .client import Client


class Family:
    def __init__(self, session: "Client", data: Dict[str, Any]):
        self.session = session
        self.data = data
        self.students: List[Student] = []

        # Parse accounts to find students
        accounts = data.get("accounts", [])
        for account in accounts:
            account_type = account.get("typeCompte")

            # If account is a Family account, students are in profile.eleves
            if account_type == "1" or account_type == "Famille":
                profile = account.get("profile", {})
                eleves = profile.get("eleves", [])
                for eleve in eleves:
                    student_id = eleve.get("id")
                    student = Student(session, student_id)
                    student.name = f"{eleve.get('prenom')} {eleve.get('nom')}"
                    self.students.append(student)

            # It's possible to have direct student links too?
            # If so, we keep the old check just in case, or simply rely on the above if that covers our case.
            elif account_type == "E":
                student_id = account.get("id")
                student = Student(session, student_id)
                student.name = f"{account.get('prenom')} {account.get('nom')}"
                self.students.append(student)

    @property
    def check_students(self) -> List[Student]:
        """Returns the list of associated students."""
        return self.students

    async def fetch(self, token: str):
        # Placeholder for specific family fetch logic if needed
        # Reference implementation might do something here but for now
        # we just want to access students.
        pass
