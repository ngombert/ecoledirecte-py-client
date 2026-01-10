import pytest
from pytest_httpx import HTTPXMock
from ecoledirecte_py_client.student import Student
from ecoledirecte_py_client.family import Family
from ecoledirecte_py_client.exceptions import MFARequiredError, LoginError


@pytest.mark.asyncio
async def test_student_login_success(
    client, httpx_mock: HTTPXMock, mock_student_login_response
):
    # Mock GTK
    httpx_mock.add_response(
        url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1&gtk=1",
        method="GET",
        headers={"Set-Cookie": "GTK=fake-gtk"},
    )

    # Mock Login
    httpx_mock.add_response(
        url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1",
        method="POST",
        json=mock_student_login_response,
        headers={"x-token": "fake-token"},
    )

    result = await client.login("user", "pass")
    assert isinstance(result, Student)
    assert result.id == 12345
    assert client.token == "fake-token"


@pytest.mark.asyncio
async def test_family_login_success(
    client, httpx_mock: HTTPXMock, mock_family_login_response
):
    # Mock GTK
    httpx_mock.add_response(
        url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1&gtk=1",
        method="GET",
        headers={"Set-Cookie": "GTK=fake-gtk"},
    )

    # Mock Login
    httpx_mock.add_response(
        url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1",
        method="POST",
        json=mock_family_login_response,
        headers={"x-token": "fake-token"},
    )

    result = await client.login("user", "pass")
    assert isinstance(result, Family)
    assert len(result.students) == 2
    assert result.students[0].id == 12345
    assert result.students[1].id == 12346


@pytest.mark.asyncio
async def test_login_mfa_required(
    client, httpx_mock: HTTPXMock, mock_mfa_required_response, mock_qcm_response
):
    # Mock GTK
    httpx_mock.add_response(
        url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1&gtk=1",
        method="GET",
        headers={"Set-Cookie": "GTK=fake-gtk"},
    )

    # Mock Login (MFA Required)
    httpx_mock.add_response(
        url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1",
        method="POST",
        json=mock_mfa_required_response,
    )

    # Mock QCM Fetch
    httpx_mock.add_response(
        url="https://api.ecoledirecte.com/v3/connexion/doubleauth.awp?verbe=get&v=4.90.1",
        method="POST",
        json=mock_qcm_response,
    )

    with pytest.raises(MFARequiredError) as excinfo:
        await client.login("user", "pass")

    assert excinfo.value.question == "What is your city?"
    assert "Paris" in excinfo.value.propositions


@pytest.mark.asyncio
async def test_login_invalid_credentials(client, httpx_mock: HTTPXMock):
    # Mock GTK
    httpx_mock.add_response(
        url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1&gtk=1",
        method="GET",
        headers={"Set-Cookie": "GTK=fake-gtk"},
    )

    # Mock Login (Invalid Credentials)
    httpx_mock.add_response(
        url="https://api.ecoledirecte.com/v3/login.awp?v=4.90.1",
        method="POST",
        json={"code": 505, "message": "Invalid credentials", "data": {}},
    )

    with pytest.raises(LoginError):
        await client.login("user", "wrong-pass")
