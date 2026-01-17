import pytest
import base64
from ecoledirecte_py_client.client import Client
from unittest.mock import MagicMock


@pytest.fixture
def mock_client():
    return MagicMock()


@pytest.fixture
async def client():
    c = Client()
    yield c
    await c.close()


@pytest.fixture
def mock_student_login_response():
    return {
        "code": 200,
        "token": "fake-token",
        "data": {
            "accounts": [
                {
                    "id": 12345,
                    "typeCompte": "E",
                    "identifiant": "jsmith",
                    "prenom": "John",
                    "nom": "Smith",
                    "nomEtablissement": "Ecole Test",
                }
            ]
        },
    }


@pytest.fixture
def mock_family_login_response():
    return {
        "code": 200,
        "token": "fake-token",
        "data": {
            "accounts": [
                {
                    "id": 67890,
                    "typeCompte": "1",
                    "identifiant": "family.smith",
                    "prenom": "Jane",
                    "nom": "Smith",
                    "profile": {
                        "eleves": [
                            {"id": 12345, "prenom": "John", "nom": "Smith"},
                            {"id": 12346, "prenom": "Alice", "nom": "Smith"},
                        ]
                    },
                }
            ]
        },
    }


@pytest.fixture
def mock_mfa_required_response():
    return {"code": 250, "message": "MFA Required", "data": {}}


@pytest.fixture
def mock_qcm_response():
    return {
        "code": 200,
        "data": {
            "question": base64.b64encode("What is your city?".encode("utf-8")).decode(
                "ascii"
            ),
            "propositions": [
                base64.b64encode("Paris".encode("utf-8")).decode("ascii"),
                base64.b64encode("Lyon".encode("utf-8")).decode("ascii"),
            ],
        },
    }


@pytest.fixture
def mock_mfa_success_response():
    return {
        "code": 200,
        "token": "mfa-token",
        "data": {
            "cn": "new_cn",
            "cv": "new_cv",
            "accounts": [
                {
                    "id": 12345,
                    "typeCompte": "E",
                    "identifiant": "jsmith",
                }
            ],
        },
    }


@pytest.fixture
def temp_files(tmp_path):
    device_file = tmp_path / "device.json"
    qcm_file = tmp_path / "qcm.json"
    return {"device_file": str(device_file), "qcm_file": str(qcm_file)}


@pytest.fixture
def mock_grades_response():
    return {
        "code": 200,
        "token": "fake-token",
        "message": "",
        "data": {
            "notes": [
                {
                    "id": 1,
                    "devoir": "Math Test",
                    "codePeriode": "A001",
                    "codeMatiere": "MATH",
                    "libelleMatiere": "Math",
                    "date": "2024-01-15",
                    "dateSaisie": "2024-01-15",
                    "valeur": "15",
                    "noteSur": "20",
                    "coef": "1",
                    "valeurisee": True,
                    "nonSignificatif": False,
                }
            ],
            "periodes": [],
        },
    }


@pytest.fixture
def mock_homework_response():
    return {
        "code": 200,
        "token": "fake-token",
        "message": "",
        "data": {
            "matieres": [
                {
                    "matiere": "Math",
                    "codeMatiere": "MATH",
                    "aFaire": {
                        "2024-01-20": [
                            {
                                "idDevoir": 1,
                                "matiere": "Math",
                                "codeMatiere": "MATH",
                                "aFaire": True,
                                "donneLe": "2024-01-15",
                                "effectue": False,
                            }
                        ]
                    },
                }
            ]
        },
    }
