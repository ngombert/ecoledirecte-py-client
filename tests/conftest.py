import pytest
import base64
from ecoledirecte_py_client.client import Client


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
