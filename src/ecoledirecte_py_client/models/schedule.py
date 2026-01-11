from datetime import date, datetime
from typing import Any, Dict, List
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ScheduleEvent(BaseModel):
    """
    A single event in the schedule (class, exam, etc.).
    """

    model_config = ConfigDict(populate_by_name=True)

    id: int
    text: str
    matiere: str
    code_matiere: str = Field(alias="codeMatiere")
    type_cours: str = Field(alias="typeCours")
    start_date: datetime = Field(
        alias="start_date"
    )  # API uses 'start_date' not camelCase? Check JSON.
    # checking captured JSON: "start_date": "2026-01-05 09:10"
    end_date: datetime = Field(alias="end_date")
    color: str
    dispensable: bool
    dispense: int
    prof: str
    salle: str
    classe: str
    classe_id: int = Field(alias="classeId")
    classe_code: str = Field(alias="classeCode")
    evenement_id: int = Field(0, alias="evenementId")
    groupe: str
    groupe_code: str = Field(alias="groupeCode")
    groupe_id: int = Field(alias="groupeId")
    is_flexible: bool = Field(False, alias="isFlexible")
    icone: str
    is_modifie: bool = Field(False, alias="isModifie")
    is_annule: bool = Field(False, alias="isAnnule")
    contenu_de_seance: bool = Field(False, alias="contenuDeSeance")
    devoir_a_faire: bool = Field(False, alias="devoirAFaire")

    @property
    def is_cancelled(self) -> bool:
        return self.is_annule

    @property
    def is_exam(self) -> bool:
        return "DS" in self.type_cours or "EXAM" in self.type_cours

    @property
    def duration_minutes(self) -> int:
        delta = self.end_date - self.start_date
        return int(delta.total_seconds() / 60)


class ScheduleResponse(BaseModel):
    """
    Response structure for schedule.
    Wraps the list [ ...events... ] returned by API.
    """

    model_config = ConfigDict(populate_by_name=True)

    events: List[ScheduleEvent] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def parse_root_list(cls, data: Any) -> Any:
        """
        The API returns a list of events directly.
        """
        if isinstance(data, list):
            return {"events": data}
        return data

    @property
    def by_date(self) -> Dict[date, List[ScheduleEvent]]:
        """Groups events by date."""
        result = {}
        sorted_events = sorted(self.events, key=lambda e: e.start_date)
        for event in sorted_events:
            d = event.start_date.date()
            if d not in result:
                result[d] = []
            result[d].append(event)
        return result
