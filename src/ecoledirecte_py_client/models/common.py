from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class Module(BaseModel):
    """
    Represents a module activated on an account (grades, messages, cloud, etc.).
    """

    model_config = ConfigDict(populate_by_name=True)

    code: str
    enable: bool
    ordre: int
    badge: int
    params: Dict[str, Any] = Field(default_factory=dict)

    @property
    def has_badge(self) -> bool:
        """Returns True if the module has active notifications."""
        return self.badge > 0


class ClasseInfo(BaseModel):
    """
    Information about a school class.
    """

    model_config = ConfigDict(populate_by_name=True)

    id: int
    code: str
    libelle: str
    est_note: int = Field(
        alias="estNote"
    )  # API returns 0 or 1, keeping as int or bool? JSON shows 1 (int)


class Subject(BaseModel):
    """
    Represents a school subject.
    Reused across grades, homework, and schedule.
    """

    model_config = ConfigDict(populate_by_name=True)

    code: str
    libelle: str
    color: Optional[str] = None

    @property
    def display_name(self) -> str:
        """Returns the label or the code if the label is empty."""
        return self.libelle or self.code


class Contact(BaseModel):
    """
    Represents a person (sender/recipient of a message, teacher, etc.).
    """

    model_config = ConfigDict(populate_by_name=True)

    id: int
    civilite: Optional[str] = None
    prenom: str
    nom: str
    particule: Optional[str] = ""
    role: str  # A=Admin, P=Prof, E=Eleve, F=Famille
    fonction_personnel: Optional[str] = Field(None, alias="fonctionPersonnel")
    liste_rouge: bool = Field(False, alias="listeRouge")
    read: Optional[bool] = None  # Specific to messages

    @property
    def full_name(self) -> str:
        """Returns the full name formatted with particle."""
        parts = [self.civilite, self.prenom, self.particule, self.nom]
        return " ".join(filter(None, parts))

    @property
    def is_teacher(self) -> bool:
        return self.role == "P"

    @property
    def is_admin(self) -> bool:
        return self.role == "A"
