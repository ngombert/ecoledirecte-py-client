"""
Tests for Client MFA handling (client.py).
"""

import pytest
import base64
from pytest_httpx import HTTPXMock

from ecoledirecte_py_client import Client
from ecoledirecte_py_client.exceptions import MFARequiredError
from tests.test_helpers import build_api_response


@pytest.mark.asyncio
class TestClientMFA:
    """Tests for Client MFA (Multi-Factor Authentication) handling."""

    async def test_mfa_required_exception(
        self, httpx_mock: HTTPXMock, temp_files, mock_qcm_response
    ):
        """Test that MFA triggers MFARequiredError when no callback is configured."""
        # Mock GTK
        httpx_mock.add_response(
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1&gtk=1",
            json={"code": 200, "token": "", "message": "", "data": {}},
        )

        # Mock login response requiring MFA
        httpx_mock.add_response(
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1",
            json=build_api_response({"codeQCM": "REQUIRED"}, code=250),
        )

        # Mock QCM question
        httpx_mock.add_response(
            url="https://api.ecoledirecte.com/v3/connexion/doubleauth.awp?verbe=get&v=4.90.1",
            json={
                "code": 200,
                "token": "",
                "message": "",
                "data": {
                    "question": base64.b64encode(
                        "Quelle est la couleur du cheval blanc d'Henri IV ?".encode()
                    ).decode(),
                    "propositions": [
                        base64.b64encode(p.encode()).decode()
                        for p in ["Blanc", "Noir", "Gris", "Marron"]
                    ],
                },
            },
        )

        client = Client(**temp_files)  # No MFA callback

        with pytest.raises(MFARequiredError) as exc_info:
            await client.login("user@example.com", "password")

        assert "cheval blanc" in exc_info.value.question.lower()
        assert len(exc_info.value.propositions) == 4

        await client.close()

    async def test_mfa_auto_submit_from_cache(
        self, httpx_mock: HTTPXMock, temp_files, mock_mfa_success_response
    ):
        """Test automatic MFA submission using cached answer."""
        # Pre-populate QCM cache
        import json

        with open(temp_files["qcm_file"], "w") as f:
            json.dump(
                {"Quelle est la couleur du cheval blanc d'Henri IV ?": ["Blanc"]}, f
            )

        # Mock GTK (Login start)
        httpx_mock.add_response(
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1&gtk=1",
            json={"code": 200, "token": "", "message": "", "data": {}},
        )

        # Mock login requiring MFA
        httpx_mock.add_response(
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1",
            json=build_api_response({"codeQCM": "REQUIRED"}, code=250),
        )

        # Mock QCM question
        httpx_mock.add_response(
            url="https://api.ecoledirecte.com/v3/connexion/doubleauth.awp?verbe=get&v=4.90.1",
            json={
                "code": 200,
                "token": "",
                "message": "",
                "data": {
                    "question": base64.b64encode(
                        "Quelle est la couleur du cheval blanc d'Henri IV ?".encode()
                    ).decode(),
                    "propositions": [
                        base64.b64encode(p.encode()).decode()
                        for p in ["Blanc", "Noir", "Gris", "Marron"]
                    ],
                },
            },
        )

        # Mock successful MFA verification
        httpx_mock.add_response(
            url="https://api.ecoledirecte.com/v3/connexion/doubleauth.awp?verbe=post&v=4.90.1",
            json=mock_mfa_success_response,
        )

        # Mock GTK (Login end - _login_with_cn_cv)
        httpx_mock.add_response(
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1&gtk=1",
            json={"code": 200, "token": "", "message": "", "data": {}},
        )

        # Mock final Login
        httpx_mock.add_response(
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1",
            json=mock_mfa_success_response,
            headers={"x-token": "mfa-token"},
        )

        client = Client(**temp_files)
        session = await client.login("user@example.com", "password")

        assert session is not None
        assert client.token == mock_mfa_success_response["token"]

        await client.close()

    async def test_mfa_callback_invocation(
        self, httpx_mock: HTTPXMock, temp_files, mock_mfa_success_response
    ):
        """Test that MFA callback is invoked when auto-submit fails."""

        def mock_callback(question: str, propositions: list) -> str:
            assert "cheval blanc" in question.lower()
            assert len(propositions) == 4
            return "Blanc"

        # Mock GTK (Login start)
        httpx_mock.add_response(
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1&gtk=1",
            json={"code": 200, "token": "", "message": "", "data": {}},
        )

        # Mock login requiring MFA
        httpx_mock.add_response(
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1",
            json=build_api_response({"codeQCM": "REQUIRED"}, code=250),
        )

        # Mock QCM question
        httpx_mock.add_response(
            url="https://api.ecoledirecte.com/v3/connexion/doubleauth.awp?verbe=get&v=4.90.1",
            json={
                "code": 200,
                "token": "",
                "message": "",
                "data": {
                    "question": base64.b64encode(
                        "Quelle est la couleur du cheval blanc d'Henri IV ?".encode()
                    ).decode(),
                    "propositions": [
                        base64.b64encode(p.encode()).decode()
                        for p in ["Blanc", "Noir", "Gris", "Marron"]
                    ],
                },
            },
        )

        # Mock successful MFA verification
        httpx_mock.add_response(
            url="https://api.ecoledirecte.com/v3/connexion/doubleauth.awp?verbe=post&v=4.90.1",
            json=mock_mfa_success_response,
        )

        # Mock GTK (Login end - _login_with_cn_cv)
        httpx_mock.add_response(
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1&gtk=1",
            json={"code": 200, "token": "", "message": "", "data": {}},
        )

        # Mock final Login
        httpx_mock.add_response(
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1",
            json=mock_mfa_success_response,
            headers={"x-token": "mfa-token"},
        )

        client = Client(**temp_files, mfa_callback=mock_callback)

        session = await client.login("user@example.com", "password")

        assert session is not None

        await client.close()

    async def test_mfa_answer_persistence(
        self, httpx_mock: HTTPXMock, temp_files, mock_mfa_success_response
    ):
        """Test that correct MFA answers are saved to cache."""
        import json

        def mock_callback(question: str, propositions: list) -> str:
            return "Blanc"

        # Mock GTK (Login start)
        httpx_mock.add_response(
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1&gtk=1",
            json={"code": 200, "token": "", "message": "", "data": {}},
        )

        # Mock login requiring MFA
        httpx_mock.add_response(
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1",
            json=build_api_response({"codeQCM": "REQUIRED"}, code=250),
        )

        # Mock QCM question
        httpx_mock.add_response(
            url="https://api.ecoledirecte.com/v3/connexion/doubleauth.awp?verbe=get&v=4.90.1",
            json={
                "code": 200,
                "token": "",
                "message": "",
                "data": {
                    "question": base64.b64encode(
                        "Quelle est la couleur du cheval blanc d'Henri IV ?".encode()
                    ).decode(),
                    "propositions": [
                        base64.b64encode(p.encode()).decode()
                        for p in ["Blanc", "Noir", "Gris", "Marron"]
                    ],
                },
            },
        )

        # Mock successful MFA
        httpx_mock.add_response(
            url="https://api.ecoledirecte.com/v3/connexion/doubleauth.awp?verbe=post&v=4.90.1",
            json=mock_mfa_success_response,
        )

        # Mock GTK (Login end - _login_with_cn_cv)
        httpx_mock.add_response(
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1&gtk=1",
            json={"code": 200, "token": "", "message": "", "data": {}},
        )

        # Mock final Login
        httpx_mock.add_response(
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1",
            json=mock_mfa_success_response,
            headers={"x-token": "mfa-token"},
        )

        client = Client(**temp_files, mfa_callback=mock_callback)
        await client.login("user@example.com", "password")

        # Check that QCM cache was saved
        with open(temp_files["qcm_file"], "r") as f:
            qcm_cache = json.load(f)

        question = "Quelle est la couleur du cheval blanc d'Henri IV ?"
        assert question in qcm_cache
        assert "Blanc" in qcm_cache[question]

        await client.close()

    async def test_submit_mfa_method(
        self, httpx_mock: HTTPXMock, temp_files, mock_mfa_success_response
    ):
        """Test the submit_mfa() public method."""
        # Setup client with pending MFA
        client = Client(**temp_files)
        client.pending_mfa_question = (
            "Quelle est la couleur du cheval blanc d'Henri IV ?"
        )
        client.token = "pending_token"
        client._temp_credentials = ("user", "pass")

        # Mock GTK for login (_login_with_cn_cv)
        httpx_mock.add_response(
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1&gtk=1",
            json={"code": 200, "token": "", "message": "", "data": {}},
        )

        # Mock MFA submission
        httpx_mock.add_response(
            url="https://api.ecoledirecte.com/v3/connexion/doubleauth.awp?verbe=post&v=4.90.1",
            json=mock_mfa_success_response,
        )

        # Mock Login (called after MFA)
        httpx_mock.add_response(
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1",
            json=mock_mfa_success_response,
            headers={"x-token": "mfa-token"},
        )

        session = await client.submit_mfa("Blanc")

        assert session is not None
        assert client.token == mock_mfa_success_response["token"]

        await client.close()
