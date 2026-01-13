from datetime import datetime
from typing import Any, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .common import ClasseInfo, Module


class AccountParameters(BaseModel):
    """
    Individual parameters for an account.
    """

    model_config = ConfigDict(populate_by_name=True)

    is_qrcode: bool = Field(False, alias="isQrcode")
    accessibilite_visuelle: bool = Field(False, alias="accessibiliteVisuelle")
    zoom_page: bool = Field(False, alias="zoomPage")
    check_authentification_secure: bool = Field(
        True, alias="checkAuthentificationSecure"
    )
    is_2fa_totp_activable: bool = Field(False, alias="is2FATOTPActivable")
    is_2fa_totp_actif: bool = Field(False, alias="is2FATOTPActif")
    # Add other parameters as needed with extra="ignore" in older pydantic versions,
    # but here we rely on default behaviour or could set extra="ignore" if API sends unexpected fields
    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class StudentProfile(BaseModel):
    """
    Profile of a student within a family account.
    """

    model_config = ConfigDict(populate_by_name=True)

    id: int
    prenom: str
    nom: str
    sexe: str
    photo: Optional[str] = None
    classe: Optional[ClasseInfo] = None
    id_etablissement: int = Field(alias="idEtablissement")
    nom_etablissement: Optional[str] = Field(None, alias="nomEtablissement")
    is_primaire: bool = Field(False, alias="isPrimaire")
    modules: List[Module] = Field(default_factory=list)

    @property
    def full_name(self) -> str:
        return f"{self.prenom} {self.nom}"

    @property
    def has_photo(self) -> bool:
        return bool(self.photo)

    @property
    def grade_level(self) -> str:
        return self.classe.code if self.classe else ""


class FamilyProfile(BaseModel):
    """
    Profile of a family account containing students.
    """

    model_config = ConfigDict(populate_by_name=True)

    email: str
    tel_portable: Optional[str] = Field(None, alias="telPortable")
    tel_portable_conjoint: Optional[str] = Field(None, alias="telPortableConjoint")
    eleves: List[StudentProfile] = Field(default_factory=list)

    @property
    def student_count(self) -> int:
        return len(self.eleves)

    @property
    def primary_phone(self) -> Optional[str]:
        return self.tel_portable or self.tel_portable_conjoint


class Account(BaseModel):
    """
    Represents an EcoleDirecte account (Student or Family).
    """

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id_login: int = Field(alias="idLogin")
    id: int
    uid: str
    identifiant: str
    type_compte: str = Field(alias="typeCompte")  # "E" or "1"/"Famille"
    code_ogec: str = Field(alias="codeOgec")
    main: bool
    last_connexion: Optional[datetime] = Field(None, alias="lastConnexion")
    civilite: Optional[str] = None
    prenom: str
    nom: str
    email: str
    is_primaire: bool = Field(False, alias="isPrimaire")
    nom_etablissement: str = Field(alias="nomEtablissement")
    logo_etablissement: Optional[str] = Field(None, alias="logoEtablissement")
    couleur_agenda_etablissement: Optional[str] = Field(
        None, alias="couleurAgendaEtablissement"
    )
    modules: List[Module] = Field(default_factory=list)
    parametres_individuels: Optional[AccountParameters] = Field(
        None, alias="parametresIndividuels"
    )
    profile: Optional[Union[FamilyProfile, StudentProfile]] = (
        None  # Parsing depends on fields
    )

    @field_validator("last_connexion", mode="before")
    @classmethod
    def parse_last_connexion(cls, v: Any) -> Optional[datetime]:
        if not v:
            return None
        if isinstance(v, datetime):
            return v
        try:
            # Format usually "YYYY-MM-DD HH:MM"
            return datetime.strptime(v, "%Y-%m-%d %H:%M")
        except ValueError:
            return None

    @property
    def full_name(self) -> str:
        parts = [self.civilite, self.prenom, self.nom]
        return " ".join(filter(None, parts))

    @property
    def is_family_account(self) -> bool:
        return self.type_compte == "1" or self.type_compte == "Famille"

    @property
    def is_student_account(self) -> bool:
        return self.type_compte == "E"

    @property
    def students(self) -> List[StudentProfile]:
        """Returns the list of students if this is a family account, else empty list."""
        if self.profile:
            return self.profile.eleves
        return []


class LoginResponse(BaseModel):
    """
    Response from the login endpoint.
    """

    model_config = ConfigDict(populate_by_name=True)

    changement_mdp: bool = Field(False, alias="changementMDP")
    nb_jour_mdp_expire: int = Field(0, alias="nbJourMdpExire")
    accounts: List[Account] = Field(default_factory=list)
    token: Optional[str] = None

    @property
    def main_account(self) -> Optional[Account]:
        """Returns the main account from the list."""
        for account in self.accounts:
            if account.main:
                return account
        return self.accounts[0] if self.accounts else None

    @property
    def password_will_expire_soon(self) -> bool:
        return 0 < self.nb_jour_mdp_expire < 7
