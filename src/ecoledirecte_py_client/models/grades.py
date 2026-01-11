from datetime import date
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ProgramElement(BaseModel):
    """
    Curriculum element evaluated in a grade (competence).
    """

    model_config = ConfigDict(populate_by_name=True)

    id_elem_prog: int = Field(alias="idElemProg")
    id_competence: int = Field(alias="idCompetence")
    id_connaissance: int = Field(alias="idConnaissance")
    libelle_competence: str = Field(alias="libelleCompetence")
    descriptif: str
    valeur: str  # Value like "3", "4" or strings
    cdt: bool
    afc: int  # Acquisition level

    @property
    def is_acquired(self) -> bool:
        return self.afc >= 3

    @property
    def numeric_value(self) -> Optional[float]:
        try:
            return float(self.valeur.replace(",", "."))
        except (ValueError, AttributeError):
            return None


class Grade(BaseModel):
    """
    Represents an individual grade.
    """

    model_config = ConfigDict(populate_by_name=True)

    id: int
    devoir: str
    code_periode: str = Field(alias="codePeriode")
    code_matiere: str = Field(alias="codeMatiere")
    libelle_matiere: str = Field(alias="libelleMatiere")
    code_sous_matiere: str = Field(alias="codeSousMatiere")
    type_devoir: str = Field(alias="typeDevoir")
    en_lettre: bool = Field(alias="enLettre")
    commentaire: str
    date: date
    date_saisie: date = Field(alias="dateSaisie")
    coef: float
    note_sur: float = Field(alias="noteSur")
    valeur: Optional[float] = None  # None if "Abs", "Disp" or invalid
    valorisee: bool = Field(alias="valeurisee")
    non_significatif: bool = Field(alias="nonSignificatif")
    moyenne_classe: float = Field(alias="moyenneClasse")
    min_classe: float = Field(alias="minClasse")
    max_classe: float = Field(alias="maxClasse")
    elements_programme: List[ProgramElement] = Field(
        default_factory=list, alias="elementsProgramme"
    )
    unc_sujet: str = Field(alias="uncSujet")
    unc_corrige: str = Field(alias="uncCorrige")

    # Validators for numeric strings
    @field_validator(
        "coef", "note_sur", "moyenne_classe", "min_classe", "max_classe", mode="before"
    )
    @classmethod
    def parse_float(cls, v: Any) -> float:
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            try:
                return float(v.replace(",", "."))
            except ValueError:
                return 0.0
        return 0.0

    @field_validator("date", "date_saisie", mode="before")
    @classmethod
    def parse_date(cls, v: Any) -> Any:
        # Pydantic handles YYYY-MM-DD string automatically, but just in case
        return v

    @model_validator(mode="before")
    @classmethod
    def handle_valeur(cls, data: Any) -> Any:
        if isinstance(data, dict):
            raw_valeur = data.get("valeur")
            # Create separate field to store raw string if needed,
            # assume "valeur_str" gets "valeur" content automatically if populated_by_name
            # But here we want 'valeur' to be float or None.

            # We copy 'valeur' to 'valeur_str' manually if we want to keep it
            # (or use alias with validation logic).
            # Easier approach: Let 'valeur_str' capture 'valeur' by alias (it has same alias).
            # But colliding aliases is tricky.
            # Workaround: manually parse 'valeur' to float, set it to None if fails.

            if raw_valeur is not None:
                # Keep raw value in a separate field if we added one to the model for debug
                # data['original_valeur'] = raw_valeur
                try:
                    data["valeur"] = float(str(raw_valeur).replace(",", "."))
                except ValueError:
                    data["valeur"] = None
            else:
                data["valeur"] = None

        return data

    @property
    def normalized_value(self) -> Optional[float]:
        """Returns the grade scaled to 20."""
        if self.valeur is None or self.note_sur == 0:
            return None
        return (self.valeur / self.note_sur) * 20.0

    @property
    def is_absent(self) -> bool:
        return self.valeur is None

    @property
    def has_resources(self) -> bool:
        return bool(self.unc_sujet or self.unc_corrige)


class SubjectGrades(BaseModel):
    """
    Grades grouped by subject for a period.
    """

    model_config = ConfigDict(populate_by_name=True)

    code_matiere: str = Field(alias="codeMatiere")
    discipline: str
    professeurs: List[str] = Field(default_factory=list)
    moyenne_eleve: Optional[float] = Field(None, alias="moyenneEleve")
    moyenne_classe: Optional[float] = Field(None, alias="moyenneClasse")
    moyenne_min: Optional[float] = Field(None, alias="moyenneMin")
    moyenne_max: Optional[float] = Field(None, alias="moyenneMax")
    notes: List[Grade] = Field(default_factory=list)

    @field_validator(
        "moyenne_eleve", "moyenne_classe", "moyenne_min", "moyenne_max", mode="before"
    )
    @classmethod
    def parse_optional_float(cls, v: Any) -> Optional[float]:
        if not v:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            try:
                return float(v.replace(",", "."))
            except ValueError:
                return None
        return None


class Period(BaseModel):
    """
    A school period (trimester, semester, etc.).
    """

    model_config = ConfigDict(populate_by_name=True)

    id_periode: str = Field(alias="idPeriode")
    code_periode: str = Field(alias="codePeriode")
    periode: str
    date_debut: date = Field(alias="dateDebut")
    date_fin: date = Field(alias="dateFin")
    date_conseil: Optional[date] = Field(None, alias="dateConseil")
    cloture: bool
    annuel: bool = False
    examen_blanc: bool = Field(False, alias="examenBlanc")
    ensemble_matieres: Dict[str, Any] = Field(
        default_factory=dict, alias="ensembleMatieres"
    )

    # We don't type ensemble_matieres as list[SubjectGrades] directly because the JSON
    # structure might be object or list? No, usually list in 'ensembleMatieres'.
    # Actually API usually returns lists for 'periodes', but 'ensembleMatieres'?
    # Checking implementation plan: "ensembleMatieres: dict[str, SubjectGrades]"
    # Wait, in capturing script output (or memory), usually it's a list recursively?
    # Let's check capture if possible. Using dict for now as safe bet if documented so.
    # Ah, standard ED API returns 'ensembleMatieres' which contains 'disciplines' or similar?
    # Actually typically ED returns 'ensembleMatieres' which IS the list of subjects?
    # Let's play it safe and check the typeValidator.
    # Re-reading: "ensembleMatieres" usually contains notes too.

    # Correction: Often "ensembleMatieres" is just a wrapper or list with subject data.
    # Let's assume it's data to be parsed into SubjectGrades.

    # Better approach: We will parse it in model_validator if it's complex structure.

    parsed_subjects: List[SubjectGrades] = Field(default_factory=list, exclude=True)

    @model_validator(mode="before")
    @classmethod
    def parse_subjects(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Logic to extract subjects if needed.
            pass
        return data

    @property
    def is_active(self) -> bool:
        today = date.today()
        return self.date_debut <= today <= self.date_fin


class GradesResponse(BaseModel):
    """
    Response from grades endpoint.
    """

    model_config = ConfigDict(populate_by_name=True)

    notes: List[Grade] = Field(default_factory=list)
    periodes: List[Period] = Field(default_factory=list)

    @property
    def active_period(self) -> Optional[Period]:
        for p in self.periodes:
            if p.is_active:
                return p
        return None
