"""
Tests for Client error handling (client.py).
"""

import pytest
from pytest_httpx import HTTPXMock
import httpx

from ecoledirecte_py_client import Client
from ecoledirecte_py_client.exceptions import (
    NetworkError,
    ApiError,
    AuthenticationError,
    LoginError,
    ResourceNotFoundError,
    ServerError,
)
from tests.test_helpers import build_error_response


@pytest.mark.asyncio
class TestClientErrors:
    """Tests for Client error handling."""

    async def test_network_error_handling(self, httpx_mock: HTTPXMock, temp_files):
        """Test handling of network errors."""
        # Simulate network error
        httpx_mock.add_exception(httpx.ConnectError("Connection failed"))

        client = Client(**temp_files)

        with pytest.raises(NetworkError):
            await client._get_gtk()

        await client.close()

    async def test_timeout_error_handling(self, httpx_mock: HTTPXMock, temp_files):
        """Test handling of timeout errors."""
        # Simulate timeout
        httpx_mock.add_exception(httpx.TimeoutException("Request timed out"))

        client = Client(**temp_files)

        with pytest.raises(NetworkError):
            await client._get_gtk()

        await client.close()

    async def test_api_error_code_500(self, httpx_mock: HTTPXMock, temp_files):
        """Test handling of HTTP 500 errors."""
        httpx_mock.add_response(
            url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1&gtk=1",
            status_code=500,
            json={"error": "Internal Server Error"},
        )

        client = Client(**temp_files)

        with pytest.raises(ServerError):
            await client._get_gtk()

        await client.close()

    async def test_api_error_code_404(self, httpx_mock: HTTPXMock, temp_files):
        """Test handling of HTTP 404 errors."""
        # Removed unused GTK mock

        httpx_mock.add_response(
            url="https://api.ecoledirecte.com/v3/notfound.awp?verbe=get&",
            status_code=404,
            json={"error": "Not Found"},
        )

        client = Client(**temp_files)
        client.token = "test_token"

        with pytest.raises(ResourceNotFoundError):
            await client.request(
                "https://api.ecoledirecte.com/v3/notfound.awp?verbe=get&"
            )

        await client.close()

    async def test_api_error_code_401(self, httpx_mock: HTTPXMock, temp_files):
        """Test handling of HTTP 401 (Unauthorized) errors."""
        # Removed unused GTK mock

        httpx_mock.add_response(
            url="https://api.ecoledirecte.com/v3/protected.awp?verbe=get&",
            status_code=401,
            json={"error": "Unauthorized"},
        )

        client = Client(**temp_files)
        client.token = "invalid_token"

        with pytest.raises(AuthenticationError):
            await client.request(
                "https://api.ecoledirecte.com/v3/protected.awp?verbe=get&"
            )

        await client.close()

    async def test_api_error_from_response_code(
        self, httpx_mock: HTTPXMock, temp_files
    ):
        """Test handling of API-specific error codes in response."""
        # Removed unused GTK mock

        # API returns 200 HTTP status but error code in JSON
        httpx_mock.add_response(
            url="https://api.ecoledirecte.com/v3/test.awp?verbe=get&",
            status_code=200,
            json=build_error_response("Custom error message", code=505),
        )

        client = Client(**temp_files)
        client.token = "test_token"

        with pytest.raises(ApiError) as exc_info:
            await client.request("https://api.ecoledirecte.com/v3/test.awp?verbe=get&")

        assert exc_info.value.code == 505
        assert "Custom error message" in str(exc_info.value)

        await client.close()

    async def test_exception_inheritance(self):
        """Test that exception hierarchy is correct."""
        # All custom exceptions should inherit from EcoleDirecteError
        from ecoledirecte_py_client.exceptions import EcoleDirecteError

        assert issubclass(NetworkError, EcoleDirecteError)
        assert issubclass(ApiError, EcoleDirecteError)
        assert issubclass(AuthenticationError, ApiError)
        assert issubclass(LoginError, AuthenticationError)
        assert issubclass(ResourceNotFoundError, ApiError)
        assert issubclass(ServerError, ApiError)
