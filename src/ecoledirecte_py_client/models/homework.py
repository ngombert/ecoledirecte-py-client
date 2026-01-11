from datetime import date
from typing import Any, Dict, List
from pydantic import BaseModel, ConfigDict, Field, model_validator


class HomeworkAssignment(BaseModel):
    """
    A single homework assignment.
    """

    model_config = ConfigDict(populate_by_name=True)

    matiere: str
    code_matiere: str = Field(alias="codeMatiere")
    a_faire: bool = Field(alias="aFaire")
    id_devoir: int = Field(alias="idDevoir")
    documents_a_faire: bool = Field(False, alias="documentsAFaire")
    donne_le: date = Field(alias="donneLe")
    pour_le: date = None  # Injected by HomeworkResponse from dict key
    effectue: bool
    interrogation: bool
    rendre_en_ligne: bool = Field(False, alias="rendreEnLigne")
    tags: List[str] = Field(default_factory=list)

    @property
    def is_test(self) -> bool:
        return self.interrogation

    @property
    def is_completed(self) -> bool:
        return self.effectue


class HomeworkResponse(BaseModel):
    """
    Response structure for homeworks.
    Wraps the dictionary of {date: [assignments]} returned by the API.
    """

    model_config = ConfigDict(populate_by_name=True)

    days: Dict[date, List[HomeworkAssignment]] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def parse_root_dict(cls, data: Any) -> Any:
        """
        The API returns a dict { "YYYY-MM-DD": [ ... ] }.
        We wrap it into 'days' field and inject pour_le into each assignment.
        """
        if isinstance(data, dict) and "days" not in data:
            # Inject pour_le into each assignment
            processed_data = {}
            for date_str, assignments in data.items():
                # Convert date string to date object
                try:
                    due_date = date.fromisoformat(date_str)
                except (ValueError, TypeError):
                    continue

                # Inject pour_le into each assignment
                updated_assignments = []
                for assignment in assignments:
                    if isinstance(assignment, dict):
                        assignment["pour_le"] = due_date
                    updated_assignments.append(assignment)

                processed_data[due_date] = updated_assignments

            return {"days": processed_data}
        return data

    @property
    def total_assignments(self) -> int:
        return sum(len(assignments) for assignments in self.days.values())

    @property
    def pending_assignments(self) -> List[HomeworkAssignment]:
        pending = []
        for day_assignments in self.days.values():
            for hw in day_assignments:
                if not hw.effectue:
                    pending.append(hw)
        return pending
