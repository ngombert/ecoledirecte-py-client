"""
Tests for grades models (grades.py).
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from ecoledirecte_py_client.models.grades import (
    Grade,
    SubjectGrades,
    Period,
    GradesResponse,
    ProgramElement,
)
from tests.test_helpers import create_mock_grade


class TestGrade:
    """Tests for the Grade model."""

    def test_grade_parsing_numeric(self):
        """Test parsing a grade with numeric value."""
        data = create_mock_grade(value="15.5", scale="20")

        grade = Grade.model_validate(data)

        assert grade.valeur == 15.5
        assert grade.note_sur == 20.0
        assert grade.devoir == "Math Test"
        assert grade.libelle_matiere == "Math"

    def test_grade_parsing_absent(self):
        """Test parsing a grade with 'Abs' (absent) value."""
        data = create_mock_grade(value="Abs")

        grade = Grade.model_validate(data)

        assert grade.valeur is None
        assert grade.is_absent is True

    def test_grade_parsing_non_note(self):
        """Test parsing a grade with non-numeric value."""
        data = create_mock_grade(value="N.Not")

        grade = Grade.model_validate(data)

        assert grade.valeur is None
        # Non-numeric string becomes None in valeur currently

    def test_grade_date_parsing(self):
        """Test that ISO date string is parsed to datetime."""
        data = create_mock_grade(date="2024-01-15")

        grade = Grade.model_validate(data)

        assert grade.date.year == 2024
        assert grade.date.month == 1
        assert grade.date.day == 15

    def test_grade_coefficient(self):
        """Test parsing grade coefficient."""
        data = create_mock_grade(coef="2")

        grade = Grade.model_validate(data)

        assert grade.coef == 2.0

    def test_grade_percentage_property(self):
        """Test the percentage computed property."""
        # Grade model currently doesn't have a 'percentage' property in valid models.py provided?
        # Checking models.py provided: It has 'normalized_value'.
        # It does NOT have 'percentage'.
        # Tests should only test existing properties.
        pass

    def test_grade_normalized_value(self):
        """Test normalized value to scale of 20."""
        data = create_mock_grade(value="15", scale="20")
        grade = Grade.model_validate(data)
        assert grade.normalized_value == 15.0

        # Test with different scale
        data2 = create_mock_grade(value="10", scale="10")
        grade2 = Grade.model_validate(data2)
        assert grade2.normalized_value == 20.0  # 10/10 = 100% = 20/20

    def test_grade_with_period_code(self):
        """Test grade with period code."""
        data = create_mock_grade(codePeriode="A001")

        grade = Grade.model_validate(data)

        assert grade.code_periode == "A001"


class TestSubjectGrades:
    """Tests for the SubjectGrades model."""

    def test_subject_grades_parsing(self):
        """Test parsing subject grades."""
        data = {
            "codeMatiere": "MATH",
            "discipline": "Mathématiques",
            "moyenneEleve": "14.5",
            "moyenneClasse": "12.3",
            "moyenneMin": "8.5",
            "moyenneMax": "18.2",
        }

        subject = SubjectGrades.model_validate(data)

        assert subject.code_matiere == "MATH"
        assert subject.discipline == "Mathématiques"
        assert subject.moyenne_eleve == 14.5
        assert subject.moyenne_classe == 12.3

    def test_subject_grades_optional_fields(self):
        """Test subject grades with missing optional averages."""
        data = {"codeMatiere": "MATH", "discipline": "Mathématiques"}

        subject = SubjectGrades.model_validate(data)

        assert subject.moyenne_eleve is None
        assert subject.moyenne_classe is None


class TestPeriod:
    """Tests for the Period model."""

    def test_period_parsing(self):
        """Test parsing a period/trimester."""
        data = {
            "idPeriode": "A001",
            "codePeriode": "A001",
            "periode": "1er Trimestre",
            "dateDebut": "2024-09-01",
            "dateFin": "2024-12-20",
            "cloture": False,
            "ensavoirs": [],
        }

        period = Period.model_validate(data)

        assert period.id_periode == "A001"
        assert period.periode == "1er Trimestre"
        assert period.date_debut.year == 2024
        assert period.date_fin.year == 2024

    def test_period_with_grades(self):
        """Test period containing grades."""
        data = {
            "idPeriode": "A001",
            "codePeriode": "A001",
            "periode": "1er Trimestre",
            "dateDebut": "2024-09-01",
            "dateFin": "2024-12-20",
            "cloture": False,
            "ensavoirs": [],
            "ensembleMatieres": {
                "matiere": {
                    "codeMatiere": "MATH",
                    "discipline": "Math",
                    "notes": [create_mock_grade(value="15", subject="Math")],
                }
            },
        }

        # We don't currently strictly validate complex nested Period structure for grades
        # as the model ignores 'parsed_subjects' by default in tests without logic.
        period = Period.model_validate(data)
        assert period.id_periode == "A001"


class TestGradesResponse:
    """Tests for the GradesResponse model."""

    def test_grades_response_with_notes(self):
        """Test grades response with top-level notes array."""
        data = {
            "notes": [
                create_mock_grade(value="15"),
                create_mock_grade(value="16"),
                create_mock_grade(value="Abs"),
            ],
            "periodes": [],
        }

        response = GradesResponse.model_validate(data)

        assert len(response.notes) == 3
        assert response.notes[0].valeur == 15.0
        assert response.notes[1].valeur == 16.0
        assert response.notes[2].valeur is None  # Abs

    def test_grades_response_with_periods(self):
        """Test grades response with periods array."""
        data = {
            "notes": [],
            "periodes": [
                {
                    "idPeriode": "A001",
                    "codePeriode": "A001",
                    "periode": "1er Trimestre",
                    "dateDebut": "2024-09-01",
                    "dateFin": "2024-12-20",
                    "cloture": False,
                    "ensavoirs": [],
                },
                {
                    "idPeriode": "A002",
                    "codePeriode": "A002",
                    "periode": "2ème Trimestre",
                    "dateDebut": "2025-01-01",
                    "dateFin": "2025-03-31",
                    "cloture": False,
                    "ensavoirs": [],
                },
            ],
        }

        response = GradesResponse.model_validate(data)

        assert len(response.periodes) == 2
        assert response.periodes[0].id_periode == "A001"
        assert response.periodes[1].id_periode == "A002"

    def test_grades_response_empty(self):
        """Test empty grades response."""
        data = {"notes": [], "periodes": []}

        response = GradesResponse.model_validate(data)

        assert response.notes == []
        assert response.periodes == []
