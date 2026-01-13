"""
Tests for common models (common.py).
"""

import pytest
from pydantic import ValidationError

from ecoledirecte_py_client.models.common import Subject, ClasseInfo, Contact, Module


class TestSubject:
    """Tests for the Subject model."""

    def test_subject_parsing(self):
        """Test parsing a subject."""
        data = {"code": "MATH", "libelle": "Mathématiques"}

        subject = Subject.model_validate(data)

        assert subject.code == "MATH"
        assert subject.libelle == "Mathématiques"

    def test_subject_minimal(self):
        """Test subject with minimal fields."""
        data = {"code": "PHYS", "libelle": "Physique"}

        subject = Subject.model_validate(data)

        assert subject.code == "PHYS"


class TestClasseInfo:
    """Tests for the ClasseInfo model."""

    def test_classe_info_parsing(self):
        """Test parsing classe information."""
        data = {"id": 10, "code": "6A", "libelle": "6ème A", "estNote": 1}

        classe = ClasseInfo.model_validate(data)

        assert classe.id == 10
        assert classe.code == "6A"
        assert classe.libelle == "6ème A"

    def test_classe_info_minimal(self):
        """Test classe with minimal fields."""
        data = {"id": 11, "code": "5B", "libelle": "5ème B", "estNote": 0}

        classe = ClasseInfo.model_validate(data)

        assert classe.code == "5B"


class TestContact:
    """Tests for the Contact model."""

    def test_contact_parsing(self):
        """Test parsing a contact."""
        data = {
            "id": 100,
            "nom": "Dupont",
            "prenom": "Marie",
            "email": "marie.dupont@school.fr",
            "role": "P",
            "civilite": "Mme",
        }

        contact = Contact.model_validate(data)

        assert contact.id == 100
        assert contact.nom == "Dupont"
        assert contact.prenom == "Marie"

    def test_contact_minimal(self):
        """Test contact with minimal fields."""
        data = {
            "id": 101,
            "nom": "Smith",
            "prenom": "John",
            "role": "E",
        }

        contact = Contact.model_validate(data)

        assert contact.nom == "Smith"


class TestModule:
    """Tests for the Module model."""

    def test_module_parsing(self):
        """Test parsing a module."""
        data = {
            "code": "VIE_SCOLAIRE",
            "enable": True,
            "params": {},
            "ordre": 1,
            "badge": 0,
        }

        module = Module.model_validate(data)

        assert module.code == "VIE_SCOLAIRE"
        assert module.enable is True
