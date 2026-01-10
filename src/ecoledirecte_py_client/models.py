from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict


class Account(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    type_compte: str = Field(alias="typeCompte")
    nom: Optional[str] = None
    prenom: Optional[str] = None
    civilite: Optional[str] = None

    # Generic field to catch other properties if needed
    data: Dict[str, Any] = Field(default_factory=dict)


class LoginResponseData(BaseModel):
    token: str
    accounts: List[Account]


class LoginResponse(BaseModel):
    code: int
    token: str
    message: str
    data: LoginResponseData


class ApiResponse(BaseModel):
    code: int
    token: Optional[str] = None
    message: Optional[str] = None
    data: Any = None
