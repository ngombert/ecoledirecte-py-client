"""
Tests for authentication models (auth.py).
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from ecoledirecte_py_client.models.auth import (
    Account,
    AccountParameters,
    StudentProfile,
    FamilyProfile,
    LoginResponse,
)
from tests.test_helpers import create_mock_account


class TestAccount:
    """Tests for the Account model."""

    def test_student_account_parsing(self):
        """Test parsing a student account."""
        data = create_mock_account(
            id=12345,
            identifiant="student@example.com",
            type_compte="E",
            nom="Doe",
            prenom="John",
            profile={
                "id": 12345,
                "prenom": "John",
                "nom": "Doe",
                "sexe": "M",
                "idEtablissement": 100,
                "classe": {"id": 1, "code": "6A", "libelle": "6ème A", "estNote": 1},
            },
        )

        account = Account.model_validate(data)

        assert account.id == 12345
        assert account.type_compte == "E"
        assert account.identifiant == "student@example.com"
        assert account.nom == "Doe"
        assert account.prenom == "John"

    def test_family_account_parsing(self):
        """Test parsing a family account."""
        data = create_mock_account(
            id=98765,
            identifiant="parent@example.com",
            type_compte="1",
            nom="Doe",
            prenom="Jane",
            profile={
                "email": "parent@example.com",
                "eleves": [
                    {
                        "id": 12345,
                        "nom": "Doe",
                        "prenom": "John",
                        "classe": {
                            "id": 1,
                            "code": "6A",
                            "libelle": "6A",
                            "estNote": 1,
                        },
                        "sexe": "M",
                        "idEtablissement": 100,
                    }
                ],
            },
        )

        account = Account.model_validate(data)

        assert account.id == 98765
        assert account.type_compte == "1"
        assert account.identifiant == "parent@example.com"

    def test_minimal_account(self):
        """Test account with minimal required fields."""
        # Using helper ensures minimal required fields are present
        data = create_mock_account(id=123, type_compte="E")

        account = Account.model_validate(data)

        assert account.id == 123
        assert account.type_compte == "E"


class TestStudentProfile:
    """Tests for the StudentProfile model."""

    def test_student_profile_parsing(self):
        """Test parsing student profile with classe info."""
        data = {
            "id": 1,
            "prenom": "John",
            "nom": "Doe",
            "sexe": "M",
            "classe": {"id": 1, "code": "6A", "libelle": "6ème A", "estNote": 1},
            "etablissement": {"id": 100, "nom": "Collège Example"},
            "idEtablissement": 100,
        }

        profile = StudentProfile.model_validate(data)

        assert profile.classe is not None
        assert profile.classe.id == 1
        assert profile.classe.code == "6A"

    def test_student_profile_optional_fields(self):
        """Test student profile with missing optional fields."""
        data = {
            "id": 1,
            "prenom": "John",
            "nom": "Doe",
            "sexe": "M",
            "idEtablissement": 100,
        }

        profile = StudentProfile.model_validate(data)

        assert profile.classe is None


class TestFamilyProfile:
    """Tests for the FamilyProfile model."""

    def test_family_profile_with_students(self):
        """Test family profile with multiple students."""
        data = {
            "email": "test@famille.com",
            "eleves": [
                {
                    "id": 1,
                    "nom": "Doe",
                    "prenom": "John",
                    "sexe": "M",
                    "classe": {"id": 1, "code": "6A", "libelle": "6A", "estNote": 1},
                    "idEtablissement": 100,
                },
                {
                    "id": 2,
                    "nom": "Doe",
                    "prenom": "Jane",
                    "sexe": "F",
                    "classe": {"id": 2, "code": "4B", "libelle": "4B", "estNote": 1},
                    "idEtablissement": 100,
                },
            ],
        }

        profile = FamilyProfile.model_validate(data)

        assert profile.eleves is not None
        assert len(profile.eleves) == 2
        assert profile.eleves[0].id == 1
        assert profile.eleves[1].id == 2

    def test_family_profile_empty_students(self):
        """Test family profile with no students."""
        data = {"email": "test@famille.com", "eleves": []}

        profile = FamilyProfile.model_validate(data)

        assert profile.eleves == []


class TestLoginResponse:
    """Tests for the LoginResponse model."""

    def test_login_response_parsing(self):
        """Test parsing a complete login response."""
        # LoginResponse model matches flattened structure or expects 'accounts' and 'token' keys directly
        data = {
            "token": "test_token_abc123",
            "accounts": [
                create_mock_account(
                    id=12345,
                    identifiant="student@example.com",
                    type_compte="E",
                    nom="Doe",
                    prenom="John",
                )
            ],
        }

        response = LoginResponse.model_validate(data)

        assert response.token == "test_token_abc123"
        assert len(response.accounts) == 1
        assert response.accounts[0].id == 12345

    def test_login_response_with_multiple_accounts(self):
        """Test login response with multiple accounts (family)."""
        data = {
            "token": "family_token",
            "accounts": [
                create_mock_account(
                    id=1,
                    type_compte="1",
                    profile={
                        "email": "parent@example.com",
                        "eleves": [
                            {
                                "id": 10,
                                "nom": "Child1",
                                "prenom": "A",
                                "sexe": "M",
                                "idEtablissement": 100,
                                "classe": {
                                    "id": 1,
                                    "code": "6A",
                                    "libelle": "6A",
                                    "estNote": 1,
                                },
                            },
                            {
                                "id": 11,
                                "nom": "Child2",
                                "prenom": "B",
                                "sexe": "F",
                                "idEtablissement": 100,
                                "classe": {
                                    "id": 1,
                                    "code": "6A",
                                    "libelle": "6A",
                                    "estNote": 1,
                                },
                            },
                        ],
                    },
                )
            ],
        }

        response = LoginResponse.model_validate(data)

        assert len(response.accounts) == 1
        assert response.accounts[0].type_compte == "1"

    def test_login_response_missing_accounts(self):
        """Test login response with empty accounts."""
        data = {"token": "token", "accounts": []}

        response = LoginResponse.model_validate(data)

        assert response.accounts == []
