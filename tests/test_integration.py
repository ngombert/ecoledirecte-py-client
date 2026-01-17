"""
Integration tests for complete workflows.
"""

import pytest
from pytest_httpx import HTTPXMock

from ecoledirecte_py_client import Client, Student, Family
from tests.test_helpers import build_api_response, create_mock_grade


@pytest.mark.asyncio
class TestIntegrationStudentLogin:
    """Integration tests for complete student login flow."""

    async def test_complete_student_login_flow(
        self, httpx_mock: HTTPXMock, temp_files, mock_student_login_response
    ):
        """Test complete login flow for a student account."""
        # Mock GTK
        httpx_mock.add_response(
            method="GET",
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1&gtk=1",
            json={"code": 200, "token": "", "message": "", "data": {}},
        )

        # Mock successful login
        httpx_mock.add_response(
            method="POST",
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1",
            json=mock_student_login_response,
        )

        client = Client(**temp_files)
        session = await client.login("student@example.com", "password")

        # Verify we got a Student instance
        assert isinstance(session, Student)
        assert session.id == mock_student_login_response["data"]["accounts"][0]["id"]
        assert client.token == mock_student_login_response["token"]

        await client.close()

    async def test_student_data_fetching_flow(
        self,
        httpx_mock: HTTPXMock,
        temp_files,
        mock_student_login_response,
        mock_grades_response,
        mock_homework_response,
    ):
        """Test complete flow of logging in and fetching student data."""
        # Mock GTK
        httpx_mock.add_response(
            method="GET",
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1&gtk=1",
            json={"code": 200, "token": "", "message": "", "data": {}},
        )

        # Mock login
        httpx_mock.add_response(
            method="POST",
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1",
            json=mock_student_login_response,
        )

        # Mock grades request
        student_id = mock_student_login_response["data"]["accounts"][0]["id"]
        httpx_mock.add_response(
            url=f"https://api.ecoledirecte.com/v3/eleves/{student_id}/notes.awp?verbe=get&",
            json=mock_grades_response,
        )

        # Mock homework request
        httpx_mock.add_response(
            url=f"https://api.ecoledirecte.com/v3/eleves/{student_id}/cahierdetexte.awp?verbe=get&",
            json=mock_homework_response,
        )

        client = Client(**temp_files)
        session = await client.login("student@example.com", "password")

        # Fetch grades
        grades = await session.get_grades()
        assert grades is not None

        # Fetch homework
        homework = await session.get_homework()
        assert homework is not None

        await client.close()


@pytest.mark.asyncio
class TestIntegrationFamilyLogin:
    """Integration tests for complete family login flow."""

    async def test_complete_family_login_flow(
        self, httpx_mock: HTTPXMock, temp_files, mock_family_login_response
    ):
        """Test complete login flow for a family account."""
        # Mock GTK
        httpx_mock.add_response(
            method="GET",
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1&gtk=1",
            json={"code": 200, "token": "", "message": "", "data": {}},
        )

        # Mock successful family login
        httpx_mock.add_response(
            method="POST",
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1",
            json=mock_family_login_response,
        )

        client = Client(**temp_files)
        session = await client.login("parent@example.com", "password")

        # Verify we got a Family instance
        assert isinstance(session, Family)
        assert len(session.students) >= 1

        await client.close()

    async def test_family_multiple_students_data_fetch(
        self, httpx_mock: HTTPXMock, temp_files, mock_family_login_response
    ):
        """Test fetching data for multiple students in a family account."""
        # Mock GTK
        httpx_mock.add_response(
            method="GET",
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1&gtk=1",
            json={"code": 200, "token": "", "message": "", "data": {}},
        )

        # Mock family login
        httpx_mock.add_response(
            method="POST",
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1",
            json=mock_family_login_response,
        )

        # Mock grades for both students
        for student_data in mock_family_login_response["data"]["accounts"][0][
            "profile"
        ]["eleves"]:
            student_id = student_data["id"]
            httpx_mock.add_response(
                url=f"https://api.ecoledirecte.com/v3/eleves/{student_id}/notes.awp?verbe=get&",
                json=build_api_response(
                    {"notes": [create_mock_grade(value="15")], "periodes": []}
                ),
            )

        client = Client(**temp_files)
        session = await client.login("parent@example.com", "password")

        # Fetch grades for each student
        for student in session.students:
            grades = await student.get_grades()
            assert grades is not None

        await client.close()


@pytest.mark.asyncio
class TestIntegrationMFAFlow:
    """Integration tests for MFA authentication flows."""

    async def test_mfa_with_callback_flow(
        self, httpx_mock: HTTPXMock, temp_files, mock_mfa_success_response
    ):
        """Test complete MFA flow with callback."""
        callback_invoked = False

        def mfa_callback(question: str, propositions: list) -> str:
            nonlocal callback_invoked
            callback_invoked = True
            return "Blanc"

        # Mock GTK
        httpx_mock.add_response(
            method="GET",
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1&gtk=1",
            json={"code": 200, "token": "", "message": "", "data": {}},
        )

        # Mock login requiring MFA
        httpx_mock.add_response(
            method="POST",
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1",
            json=build_api_response({"codeQCM": "REQUIRED"}, code=250),
        )

        # Mock QCM question
        import base64

        httpx_mock.add_response(
            method="POST",
            url="https://api.ecoledirecte.com/v3/connexion/doubleauth.awp?verbe=get&v=4.90.1",
            json={
                "code": 200,
                "token": "",
                "message": "",
                "data": {
                    "question": base64.b64encode(
                        "Quelle est la couleur du cheval blanc d'Henri IV ?".encode(
                            "utf-8"
                        )
                    ).decode("ascii"),
                    "propositions": [
                        base64.b64encode("Blanc".encode("utf-8")).decode("ascii"),
                        base64.b64encode("Noir".encode("utf-8")).decode("ascii"),
                        base64.b64encode("Gris".encode("utf-8")).decode("ascii"),
                        base64.b64encode("Marron".encode("utf-8")).decode("ascii"),
                    ],
                },
            },
        )

        # Mock successful MFA verification
        httpx_mock.add_response(
            method="POST",
            url="https://api.ecoledirecte.com/v3/connexion/doubleauth.awp?verbe=post&v=4.90.1",
            json=mock_mfa_success_response,
        )

        # Mock second GTK for cn/cv login
        httpx_mock.add_response(
            method="GET",
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1&gtk=1",
            json={"code": 200, "token": "", "message": "", "data": {}},
        )

        # Mock final login with cn/cv
        httpx_mock.add_response(
            method="POST",
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1",
            json=mock_mfa_success_response,
        )

        client = Client(**temp_files, mfa_callback=mfa_callback)
        session = await client.login("user@example.com", "password")

        # Verify callback was invoked and login succeeded
        assert callback_invoked is True
        assert session is not None

        await client.close()

    async def test_device_token_persistence_after_mfa(
        self, httpx_mock: HTTPXMock, temp_files, mock_mfa_success_response
    ):
        """Test that device tokens are persisted after successful MFA."""
        import json

        def mfa_callback(question: str, propositions: list) -> str:
            return "Blanc"

        # Mock GTK
        httpx_mock.add_response(
            method="GET",
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1&gtk=1",
            json={"code": 200, "token": "", "message": "", "data": {}},
        )

        # Mock login requiring MFA
        httpx_mock.add_response(
            method="POST",
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1",
            json=build_api_response({"codeQCM": "REQUIRED"}, code=250),
        )

        # Mock QCM
        import base64

        httpx_mock.add_response(
            method="POST",
            url="https://api.ecoledirecte.com/v3/connexion/doubleauth.awp?verbe=get&v=4.90.1",
            json={
                "code": 200,
                "token": "",
                "message": "",
                "data": {
                    "question": base64.b64encode("Test?".encode("utf-8")).decode(
                        "ascii"
                    ),
                    "propositions": [
                        base64.b64encode("Blanc".encode("utf-8")).decode("ascii"),
                        base64.b64encode("Noir".encode("utf-8")).decode("ascii"),
                    ],
                },
            },
        )

        # Mock successful MFA with device tokens
        httpx_mock.add_response(
            method="POST",
            url="https://api.ecoledirecte.com/v3/connexion/doubleauth.awp?verbe=post&v=4.90.1",
            json=mock_mfa_success_response,
        )

        # Mock second GTK for cn/cv login
        httpx_mock.add_response(
            method="GET",
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1&gtk=1",
            json={"code": 200, "token": "", "message": "", "data": {}},
        )

        # Mock final login with cn/cv
        httpx_mock.add_response(
            method="POST",
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1",
            json=mock_mfa_success_response,
        )

        client = Client(**temp_files, mfa_callback=mfa_callback)
        await client.login("user@example.com", "password")

        # Verify device tokens were saved
        with open(temp_files["device_file"], "r") as f:
            device_data = json.load(f)

        assert "cn" in device_data
        assert "cv" in device_data

        await client.close()


@pytest.mark.asyncio
class TestIntegrationEndToEnd:
    """End-to-end integration tests."""

    async def test_login_fetch_all_data_student(
        self, httpx_mock: HTTPXMock, temp_files, mock_student_login_response
    ):
        """Test complete workflow: login + fetch all data types."""
        # Mock GTK
        httpx_mock.add_response(
            method="GET",
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1&gtk=1",
            json={"code": 200, "token": "", "message": "", "data": {}},
        )

        # Mock login
        httpx_mock.add_response(
            method="POST",
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1",
            json=mock_student_login_response,
        )

        student_id = mock_student_login_response["data"]["accounts"][0]["id"]

        # Mock all data endpoints
        httpx_mock.add_response(
            url=f"https://api.ecoledirecte.com/v3/eleves/{student_id}/notes.awp?verbe=get&",
            json=build_api_response({"notes": [], "periodes": []}),
        )
        httpx_mock.add_response(
            url=f"https://api.ecoledirecte.com/v3/eleves/{student_id}/cahierdetexte.awp?verbe=get&",
            json=build_api_response({"matieres": []}),
        )
        httpx_mock.add_response(
            url=f"https://api.ecoledirecte.com/v3/E/{student_id}/emploidutemps.awp?verbe=get&",
            json=build_api_response([]),
        )
        httpx_mock.add_response(
            url=f"https://api.ecoledirecte.com/v3/eleves/{student_id}/messages.awp?verbe=getall&typeRecuperation=received&orderBy=date&order=desc&page=0&itemsPerPage=20&onlyRead=&query=&idClasseur=0",
            json=build_api_response({"messages": {"received": [], "sent": []}}),
        )

        client = Client(**temp_files)
        session = await client.login("student@example.com", "password")

        # Fetch all data types
        grades = await session.get_grades()
        homework = await session.get_homework()
        schedule = await session.get_schedule("2024-01-15", "2024-01-20")
        messages = await session.get_messages()

        # All should succeed without errors
        assert grades is not None
        assert homework is not None
        assert schedule is not None
        assert messages is not None

        await client.close()
