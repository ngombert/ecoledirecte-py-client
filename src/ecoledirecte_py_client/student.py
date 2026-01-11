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

    async def get_homework(self) -> Dict[str, Any]:
        """
        Retrieves homeworks.
        Implementation based on `Student.js`.
        """
        url = f"https://api.ecoledirecte.com/v3/Eleves/{self.id}/cahierdetexte.awp?verbe=get&"
        response = await self.session.request(url)
        return response.get("data", {})

    async def get_schedule(
        self, start_date: str, end_date: str
    ) -> List[Dict[str, Any]]:
        """
        Retrieves schedule.
        dates should be formatted/typed appropriately.
        """
        url = (
            f"https://api.ecoledirecte.com/v3/E/{self.id}/emploidutemps.awp?verbe=get&"
        )
        payload = {"dateDebut": start_date, "dateFin": end_date}
        response = await self.session.request(url, payload)
        return response.get("data", [])

    async def get_messages(self) -> Dict[str, Any]:
        url = f"https://api.ecoledirecte.com/v3/eleves/{self.id}/messages.awp?verbe=getall&typeRecuperation=received&orderBy=date&order=desc&page=0&itemsPerPage=20&onlyRead=&query=&idClasseur=0"
        response = await self.session.request(url)
        return response.get("data", {})
