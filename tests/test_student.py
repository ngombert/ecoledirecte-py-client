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
        "data": {
            "matieres": [
                {
                    "matiere": "Maths",
                    "aFaire": {
                        "2026-01-10": [
                            {
                                "idDevoir": 1,
                                "matiere": "Maths",
                                "aFaire": True,
                                "donneLe": "2026-01-08",
                                "effectue": False,
                            }
                        ]
                    },
                }
            ]
        },
    }

    httpx_mock.add_response(
        url="https://api.ecoledirecte.com/v3/eleves/12345/cahierdetexte.awp?verbe=get&",
        method="POST",
        json=mock_response,
    )

    homework = await student.get_homework()
    assert isinstance(homework, list)


@pytest.mark.asyncio
async def test_get_schedule(client, httpx_mock: HTTPXMock):
    from tests.test_helpers import create_mock_schedule_event

    student = Student(client, 12345)
    client.token = "fake-token"

    mock_response = {
        "code": 200,
        "data": [
            create_mock_schedule_event(
                subject="Maths", start="2026-01-10 08:00:00", end="2026-01-10 09:00:00"
            )
        ],
    }

    httpx_mock.add_response(
        url="https://api.ecoledirecte.com/v3/E/12345/emploidutemps.awp?verbe=get&",
        method="POST",
        json=mock_response,
    )

    schedule = await student.get_schedule("2026-01-10", "2026-01-11")
    assert len(schedule) == 1
    assert schedule[0].text == "Maths"
