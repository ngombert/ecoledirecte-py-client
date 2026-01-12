from datetime import date, datetime
from typing import Any, Dict, List
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .common import Contact


class MessageFile(BaseModel):
    """
    Attachment to a message.
    """

    model_config = ConfigDict(populate_by_name=True)

    id: int
    libelle: str
    date: date
    type: str
    signature_demandee: bool = Field(False, alias="signatureDemandee")
    etat_signatures: List[Any] = Field(default_factory=list, alias="etatSignatures")
    signature: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, v: Any) -> Any:
        # Just reliance on pydantic
        return v


class Message(BaseModel):
    """
    A message.
    """

    model_config = ConfigDict(populate_by_name=True)

    id: int
    response_id: int = Field(alias="responseId")
    forward_id: int = Field(alias="forwardId")
    mtype: str  # "received", "sent"
    read: bool
    id_dossier: int = Field(alias="idDossier")
    id_classeur: int = Field(alias="idClasseur")
    transferred: bool
    answered: bool
    to_cc_cci: str  # "cci"
    brouillon: bool
    can_answer: bool = Field(alias="canAnswer")
    subject: str
    content: str
    date: datetime
    to: List[Contact] = Field(default_factory=list)
    from_sender: Contact = Field(alias="from")
    files: List[MessageFile] = Field(default_factory=list)

    @field_validator("date", mode="before")
    @classmethod
    def parse_datetime(cls, v: Any) -> Any:
        if isinstance(v, str):
            # Format "YYYY-MM-DD HH:MM:SS" -> replace space with T
            # or just pydantic might handle it?
            # safe bet:
            if " " in v and "T" not in v:
                return v.replace(" ", "T")
        return v

    @property
    def sender_name(self) -> str:
        return self.from_sender.full_name


class MessagesResponse(BaseModel):
    """
    Response from messages endpoint.
    """

    model_config = ConfigDict(populate_by_name=True)

    classeurs: List[Any] = Field(default_factory=list)
    messages: Dict[str, List[Message]] = Field(default_factory=dict)

    # Helper properties for easy access
    @property
    def received_messages(self) -> List[Message]:
        return self.messages.get("received", [])

    @property
    def sent_messages(self) -> List[Message]:
        return self.messages.get("sent", [])

    @property
    def unread_count(self) -> int:
        return sum(1 for m in self.received_messages if not m.read)
