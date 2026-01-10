import pytest
from pytest_httpx import HTTPXMock
from ecoledirecte_py_client.student import Student


@pytest.mark.asyncio
async def test_get_grades(client, httpx_mock: HTTPXMock):
    student = Student(client, 12345)
    client.token = "fake-token"

    mock_response = {
        "code": 200,
        "data": {
            "notes": [{"codeMatiere": "FRAN", "valeur": "15"}],
            "periodes": [
                {"idPeriode": "A001", "nomPeriode": "Trimestre 1"},
                {"idPeriode": "A002", "nomPeriode": "Trimestre 2"},
            ],
        },
    }

    httpx_mock.add_response(
        url="https://api.ecoledirecte.com/v3/eleves/12345/notes.awp?verbe=get&",
        method="POST",
        json=mock_response,
    )

    # Test all grades
    grades = await student.get_grades()
    assert len(grades) == 1
    assert grades[0]["codeMatiere"] == "FRAN"

    # Test filtered by quarter
    httpx_mock.add_response(
        url="https://api.ecoledirecte.com/v3/eleves/12345/notes.awp?verbe=get&",
        method="POST",
        json=mock_response,
    )
    q1_grades = await student.get_grades(quarter=1)
    assert q1_grades["idPeriode"] == "A001"


@pytest.mark.asyncio
async def test_get_homework(client, httpx_mock: HTTPXMock):
    student = Student(client, 12345)
    client.token = "fake-token"

    mock_response = {
        "code": 200,
        "data": {"2026-01-10": [{"matiere": "Maths", "texte": "Exercice 1"}]},
    }

    httpx_mock.add_response(
        url="https://api.ecoledirecte.com/v3/Eleves/12345/cahierdetexte.awp?verbe=get&",
        method="POST",
        json=mock_response,
    )

    homework = await student.get_homework()
    assert "2026-01-10" in homework


@pytest.mark.asyncio
async def test_get_schedule(client, httpx_mock: HTTPXMock):
    student = Student(client, 12345)
    client.token = "fake-token"

    mock_response = {
        "code": 200,
        "data": [{"matiere": "Maths", "start_date": "2026-01-10 08:00"}],
    }

    httpx_mock.add_response(
        url="https://api.ecoledirecte.com/v3/E/12345/emploidutemps.awp?verbe=get&",
        method="POST",
        json=mock_response,
    )

    schedule = await student.get_schedule("2026-01-10", "2026-01-11")
    assert len(schedule) == 1
    assert schedule[0]["matiere"] == "Maths"
