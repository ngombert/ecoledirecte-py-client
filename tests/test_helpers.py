"""
Helper functions for EcoleDirecte tests.
"""

import json
from pathlib import Path
from typing import Dict, Any


def load_api_response(filename: str) -> Dict[str, Any]:
    """
    Load an API response from the api_responses directory.

    Args:
        filename: Name of the JSON file (with or without .json extension)

    Returns:
        Parsed JSON data
    """
    api_responses_dir = Path(__file__).parent.parent / "api_responses"

    if not filename.endswith(".json"):
        filename = f"{filename}.json"

    filepath = api_responses_dir / filename

    if not filepath.exists():
        raise FileNotFoundError(f"API response file not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def build_api_response(
    data: Any, code: int = 200, token: str = "", message: str = ""
) -> Dict[str, Any]:
    """
    Build a standard EcoleDirecte API response.

    Args:
        data: The response data
        code: HTTP status code (default: 200)
        token: Authentication token (default: "")
        message: Response message (default: "")

    Returns:
        Formatted API response dictionary
    """
    return {"code": code, "token": token, "message": message, "data": data}


def build_error_response(message: str, code: int = 500) -> Dict[str, Any]:
    """
    Build an error API response.

    Args:
        message: Error message
        code: Error code (default: 500)

    Returns:
        Formatted error response dictionary
    """
    return {"code": code, "token": "", "message": message, "data": {}}


def assert_grade_valid(grade_dict: Dict[str, Any]) -> None:
    """
    Assert that a grade dictionary has required fields.

    Args:
        grade_dict: Grade data to validate
    """
    required_fields = ["devoir", "date", "valeur", "noteSur"]
    for field in required_fields:
        assert field in grade_dict, f"Grade missing required field: {field}"


def assert_homework_valid(homework_dict: Dict[str, Any]) -> None:
    """
    Assert that a homework dictionary has required fields.

    Args:
        homework_dict: Homework data to validate
    """
    required_fields = ["aFaire", "donneLe", "matiere"]
    for field in required_fields:
        assert field in homework_dict, f"Homework missing required field: {field}"


def assert_schedule_event_valid(event_dict: Dict[str, Any]) -> None:
    """
    Assert that a schedule event dictionary has required fields.

    Args:
        event_dict: Schedule event data to validate
    """
    required_fields = ["text", "start_date", "end_date"]
    for field in required_fields:
        assert field in event_dict, f"Schedule event missing required field: {field}"


def assert_message_valid(message_dict: Dict[str, Any]) -> None:
    """
    Assert that a message dictionary has required fields.

    Args:
        message_dict: Message data to validate
    """
    required_fields = ["id", "subject", "date"]
    for field in required_fields:
        assert field in message_dict, f"Message missing required field: {field}"


def create_mock_grade(
    value: str = "15",
    scale: str = "20",
    subject: str = "Math",
    date: str = "2024-01-15",
    **kwargs,
) -> Dict[str, Any]:
    """
    Create a mock grade dictionary for testing.

    Args:
        value: Grade value
        scale: Grade scale (out of)
        subject: Subject name
        date: Grade date
        **kwargs: Additional fields to include

    Returns:
        Mock grade dictionary
    """
    grade = {
        "id": 1,
        "devoir": f"{subject} Test",
        "codePeriode": "A001",
        "codeMatiere": subject.upper(),
        "libelleMatiere": subject,
        "codeSousMatiere": "",
        "typeDevoir": "Devoir",
        "enLettre": False,
        "commentaire": "",
        "date": date,
        "dateSaisie": date,
        "valeur": value,
        "noteSur": scale,
        "coef": "1",
        "valeurisee": True,
        "nonSignificatif": False,
        "moyenneClasse": "12.5",
        "minClasse": "8.0",
        "maxClasse": "18.0",
        "elementsProgramme": [],
        "uncSujet": "",
        "uncCorrige": "",
    }
    grade.update(kwargs)
    return grade


def create_mock_homework(
    subject: str = "Math",
    description: str = "Exercises 1-5",
    due_date: str = "2024-01-20",
    given_date: str = "2024-01-15",
    done: bool = False,
    **kwargs,
) -> Dict[str, Any]:
    """
    Create a mock homework dictionary for testing.

    Args:
        subject: Subject name
        description: Homework description (used for legacy or if content field exists)
        due_date: Due date
        given_date: Date it was given
        done: Whether it's completed
        **kwargs: Additional fields to include

    Returns:
        Mock homework dictionary
    """
    homework = {
        "idDevoir": 1,
        "matiere": subject,
        "codeMatiere": subject.upper(),
        "aFaire": True,  # Model expects bool
        "donneLe": given_date,
        "effectue": done,
        "interrogation": False,
        "documentsAFaire": False,
        "rendreEnLigne": False,
        "tags": [],
    }
    homework.update(kwargs)
    return homework


def create_mock_schedule_event(
    subject: str = "Math",
    start: str = "2024-01-15 08:00:00",
    end: str = "2024-01-15 09:00:00",
    room: str = "A101",
    **kwargs,
) -> Dict[str, Any]:
    """
    Create a mock schedule event dictionary for testing.

    Args:
        subject: Subject name
        start: Start datetime
        end: End datetime
        room: Room number
        **kwargs: Additional fields to include

    Returns:
        Mock schedule event dictionary
    """
    event = {
        "id": 1,
        "text": subject,
        "matiere": subject.upper(),
        "codeMatiere": subject.upper(),
        "typeCours": "COURS",
        "start_date": start,
        "end_date": end,
        "color": "#FF0000",
        "dispensable": False,
        "dispense": 0,
        "prof": "M. Teacher",
        "salle": room,
        "classe": "3A",
        "classeId": 1,
        "classeCode": "3A",
        "evenementId": 0,
        "groupe": "",
        "groupeCode": "",
        "groupeId": 0,
        "icone": "fa-book",
        "isFlexible": False,
        "isModifie": False,
        "isAnnule": False,
        "contenuDeSeance": False,
        "devoirAFaire": False,
    }
    event.update(kwargs)
    return event


def create_mock_account(
    id: int = 12345,
    identifiant: str = "user@example.com",
    type_compte: str = "E",
    nom: str = "Doe",
    prenom: str = "John",
    **kwargs,
) -> Dict[str, Any]:
    """
    Create a mock account dictionary for testing.

    Args:
        id: Account ID
        identifiant: Username/Email
        type_compte: Account type ("E" or "1")
        nom: Last name
        prenom: First name
        **kwargs: Additional fields to include

    Returns:
        Mock account dictionary
    """
    account = {
        "id": id,
        "idLogin": id,
        "identifiant": identifiant,
        "typeCompte": type_compte,
        "codeOgec": "0750001A",
        "main": True,
        "lastConnexion": "2024-01-15 10:00",
        "civilite": "M.",
        "prenom": prenom,
        "nom": nom,
        "email": identifiant,
        "uid": str(id),
        "isPrimaire": False,
        "nomEtablissement": "College Default",
        "logoEtablissement": "",
        "couleurAgendaEtablissement": "",
        "modules": [],
        "parametresIndividuels": {},
    }

    if type_compte == "1":
        account["profile"] = {"email": identifiant, "eleves": []}

    account.update(kwargs)
    return account


def create_mock_message(
    id: int = 1,
    subject: str = "Test Message",
    content: str = "Content",
    sender: str = "Teacher",
    date: str = "2024-01-15 10:00:00",
    read: bool = False,
    mtype: str = "received",
    **kwargs,
) -> Dict[str, Any]:
    """
    Create a mock message dictionary for testing.

    Args:
        id: Message ID
        subject: Message subject
        content: Message content
        sender: Sender name (simplified)
        date: Message date
        read: Whether it's read
        mtype: Message type ("received" or "sent")
        **kwargs: Additional fields to include

    Returns:
        Mock message dictionary
    """
    message = {
        "id": id,
        "responseId": 0,
        "forwardId": 0,
        "mtype": mtype,
        "read": read,
        "idDossier": 0,
        "idClasseur": 0,
        "transferred": False,
        "answered": False,
        "to_cc_cci": "",
        "brouillon": False,
        "canAnswer": True,
        "subject": subject,
        "content": content,
        "date": date,
        "to": [],
        "from": {
            "id": 99,
            "civilite": "M.",
            "prenom": "Jean",
            "nom": sender,
            "role": "P",
        },
        "files": [],
    }
    message.update(kwargs)
    return message
