"""
Tests for Client authentication (client.py).
"""

import pytest
from pytest_httpx import HTTPXMock

from ecoledirecte_py_client import Client
from ecoledirecte_py_client.exceptions import LoginError, ApiError
from tests.test_helpers import build_api_response, build_error_response


@pytest.mark.asyncio
class TestClientAuthentication:
    """Tests for Client authentication methods."""

    async def test_get_gtk(self, httpx_mock: HTTPXMock, temp_files):
        """Test GTK retrieval from API."""
        # Mock the GTK endpoint
        httpx_mock.add_response(
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1&gtk=1",
            json={"code": 200, "token": "", "message": "", "data": {}},
            headers={"Set-Cookie": "GTK=test_gtk_value"},
        )

        client = Client(**temp_files)
        await client._get_gtk()

        assert "x-gtk" in client.headers
        await client.close()

    async def test_login_success_student(
        self, httpx_mock: HTTPXMock, temp_files, mock_student_login_response
    ):
        """Test successful login for student account."""
        # Mock GTK
        httpx_mock.add_response(
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1&gtk=1",
            json={"code": 200, "token": "", "message": "", "data": {}},
        )

        # Mock login
        httpx_mock.add_response(
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1",
            json=mock_student_login_response,
        )

        client = Client(**temp_files)
        session = await client.login("student@example.com", "password")

        assert session is not None
        assert client.token == mock_student_login_response["token"]
        await client.close()

    async def test_login_invalid_credentials(self, httpx_mock: HTTPXMock, temp_files):
        """Test login with invalid credentials."""
        # Mock GTK
        httpx_mock.add_response(
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1&gtk=1",
            json={"code": 200, "token": "", "message": "", "data": {}},
        )

        # Mock failed login
        httpx_mock.add_response(
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1",
            json=build_error_response("Identifiants incorrects", code=505),
        )

        client = Client(**temp_files)

        with pytest.raises(LoginError):
            await client.login("wrong@example.com", "wrongpass")

        await client.close()

    async def test_login_with_device_tokens(
        self, httpx_mock: HTTPXMock, temp_files, mock_student_login_response
    ):
        """Test login using saved device tokens (cn, cv)."""
        # Mock GTK
        httpx_mock.add_response(
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1&gtk=1",
            json={"code": 200, "token": "", "message": "", "data": {}},
        )

        # Mock login with device tokens
        httpx_mock.add_response(
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1",
            json=mock_student_login_response,
        )

        client = Client(**temp_files)
        session = await client.login(
            "student@example.com", "password", cn="saved_cn", cv="saved_cv"
        )

        assert session is not None
        await client.close()

    async def test_token_update(self, temp_files):
        """Test token update mechanism."""
        client = Client(**temp_files)

        new_token = "new_token_12345"
        client._update_token(new_token)

        assert client.token == new_token
        assert "x-token" in client.client.headers
        assert client.client.headers["x-token"] == new_token

        await client.close()

    async def test_gtk_header_removal_after_token(self, temp_files):
        """Test that GTK header is removed after receiving a token."""
        client = Client(**temp_files)

        # Simulate GTK being set
        client.headers["x-gtk"] = "test_gtk"
        client.client.headers["x-gtk"] = "test_gtk"

        # Update token
        client._update_token("new_token")

        # GTK should be removed
        assert "x-gtk" not in client.client.headers

        await client.close()

    async def test_encode_string(self, temp_files):
        """Test custom string encoding function."""
        client = Client(**temp_files)

        encoded = client._encode_string("test")

        # Should be base64 encoded
        assert isinstance(encoded, str)
        assert len(encoded) > 0

        await client.close()

    async def test_request_method(self, httpx_mock: HTTPXMock, temp_files):
        """Test the generic request method."""
        # Mock API request
        httpx_mock.add_response(
            url="https://api.ecoledirecte.com/v3/test.awp?verbe=get&",
            json=build_api_response({"test": "data"}),
        )

        client = Client(**temp_files)
        client.token = "test_token"

        response = await client.request(
            "https://api.ecoledirecte.com/v3/test.awp?verbe=get&"
        )

        assert response["data"]["test"] == "data"

        await client.close()

    async def test_api_error_handling(self, httpx_mock: HTTPXMock, temp_files):
        """Test handling of API error responses."""
        # Mock error response
        httpx_mock.add_response(
            url="https://api.ecoledirecte.com/v3/error.awp?verbe=get&",
            json=build_error_response("Something went wrong", code=500),
        )

        client = Client(**temp_files)
        client.token = "test_token"

        with pytest.raises(ApiError) as exc_info:
            await client.request("https://api.ecoledirecte.com/v3/error.awp?verbe=get&")

        assert exc_info.value.code == 500

        await client.close()
