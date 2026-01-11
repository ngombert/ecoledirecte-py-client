import httpx
import json
import base64
from typing import Optional, Union, Dict, Any
from .models import Account
from .exceptions import (
    ApiError,
    LoginError,
    MFARequiredError,
    NetworkError,
    AuthenticationError,
    ResourceNotFoundError,
    ServerError,
    EcoleDirecteError,
)
from .student import Student
from .family import Family
from .managers.grades_manager import GradesManager


class Client:
    def __init__(self):
        self.token: Optional[str] = None
        # Headers from reference implementation
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "fr-FR,fr;q=0.9",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded",
            "DNT": "1",
            "Origin": "https://www.ecoledirecte.com",
            "Priority": "1",
            "Referer": "https://www.ecoledirecte.com/",
            "Sec-Ch-Ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            "X-Requested-With": "XMLHttpRequest",
        }
        self.client = httpx.AsyncClient(
            headers=self.headers, verify=False, timeout=30.0, trust_env=False
        )
        self.accounts: list[Account] = []
        self.api_version = "4.90.1"

        # Managers
        self.grades = GradesManager(self)
        self.cn: Optional[str] = None
        self.cv: Optional[str] = None

    async def _get_gtk(self):
        """Retrieves the GTK (Global Token Key) and sets up session cookies."""
        url = "https://api.ecoledirecte.com/v3/login.awp"
        params = {"v": self.api_version, "gtk": "1"}

        if "x-gtk" in self.client.headers:
            del self.client.headers["x-gtk"]
        if "x-gtk" in self.headers:
            del self.headers["x-gtk"]

        try:
            response = await self.client.get(url, params=params)

            # We don't use _handle_response here because this endpoint might behave differently
            # or we just want the cookies/GTK specifically without full error parsing yet?
            # Actually, standard error handling should apply, but let's keep it specific for GTK extraction first.

            gtk_value = response.cookies.get("GTK")
            if gtk_value:
                self.headers["x-gtk"] = gtk_value
                self.client.headers.update({"x-gtk": gtk_value})
                # print(f"DEBUG: GTK found: {gtk_value}")

        except httpx.RequestError as e:
            raise NetworkError(f"Failed to get GTK: {e}")

    def _encode_string(self, string: str) -> str:
        """Custom encoding from reference implementation."""
        return (
            string.replace("%", "%25")
            .replace("&", "%26")
            .replace("+", "%2B")
            .replace("\\", "\\\\\\")
            .replace("\\\\", "\\\\\\\\")
            .replace('"', '\\"')
        )

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """
        Centralized response handling.
        Checks HTTP status and API 'code' field.
        """
        try:
            resp_json = response.json()
        except json.JSONDecodeError:
            raise ApiError("Invalid JSON response")

        code = resp_json.get("code")
        message = resp_json.get("message", "Unknown error")

        if response.status_code == 401 or response.status_code == 403:
            raise AuthenticationError(f"HTTP {response.status_code}: Unauthorized")
        elif response.status_code == 404:
            raise ResourceNotFoundError(f"HTTP 404: Not Found - {response.url}")
        elif response.status_code >= 500:
            raise ServerError(f"HTTP {response.status_code}: Server Error")
        elif response.status_code != 200:
            raise ApiError(
                f"HTTP {response.status_code}: Unexpected Error",
                code=response.status_code,
            )

        try:
            resp_json = response.json()
        except json.JSONDecodeError:
            raise ApiError("Invalid JSON response")

        # Capture token from headers or body if present
        if "x-token" in response.headers:
            self._update_token(response.headers["x-token"])

        # Body token update disabled to match reference implementation

        code = resp_json.get("code")

        if code == 200:
            return resp_json

        message = resp_json.get("message", "Unknown error")
        # data = resp_json.get("data")

        if code == 250:  # ED_MFA_REQUIRED
            # This is handled specifically in login, but if it happens elsewhere:
            # For general requests, it might mean session expired or needs re-auth?
            # Usually only happens during login.
            # We will raise it generically here, but Login flow catches it specifically.
            raise ApiError(f"MFA Required (Unexpected context): {message}", code=code)
        elif code == 505:  # Invalid credentials or session
            raise AuthenticationError(
                f"Invalid Credentials or Session: {message}", code=code
            )
        elif code == 520 or code == 525:
            # 520: Token invalide ?
            raise AuthenticationError(f"Token Invalid or Expired: {message}", code=code)

        raise ApiError(f"API Error {code}: {message}", code=code)

    def _update_token(self, token: str):
        if token and token != self.token:
            self.token = token
            self.headers["x-token"] = token
            self.client.headers.update({"x-token": token})

            # Reference implementation removes x-gtk after receiving a token
            if "x-gtk" in self.client.headers:
                del self.client.headers["x-gtk"]
            if "x-gtk" in self.headers:
                del self.headers["x-gtk"]

    async def login(
        self, username, password, cn: Optional[str] = None, cv: Optional[str] = None
    ) -> Union[Student, Family]:
        await self._get_gtk()
        self._temp_credentials = (username, password)
        self.cn = cn
        self.cv = cv
        url = "https://api.ecoledirecte.com/v3/login.awp"

        # Manual construction heavily preferred
        encoded_user = self._encode_string(username)
        encoded_pass = self._encode_string(password)

        if cn and cv:
            body = f'data={{"identifiant":"{encoded_user}", "motdepasse":"{encoded_pass}", "isRelogin": false, "cn":"{cn}", "cv":"{cv}", "uuid": "", "fa": [{{"cn": "{cn}", "cv": "{cv}"}}]}}'
        else:
            body = f'data={{"identifiant":"{encoded_user}", "motdepasse":"{encoded_pass}", "isRelogin": false}}'

        try:
            response = await self.client.post(
                url, params={"v": self.api_version}, content=body
            )

            # Capture token immediately as it is needed for MFA steps
            if "x-token" in response.headers:
                self._update_token(response.headers["x-token"])

            resp_json = response.json()
            # Body token ignored in favor of header token as per reference

            code = resp_json.get("code")

            if code == 250:
                # Fetch QCM Question
                qcm = await self._get_qcm_connexion()
                question = base64.b64decode(qcm.get("question", "")).decode("utf-8")
                propositions = [
                    base64.b64decode(p).decode("utf-8")
                    for p in qcm.get("propositions", [])
                ]
                raise MFARequiredError(
                    "MFA Required", question=question, propositions=propositions
                )

            # Delegate to standard handler for other cases (success or other errors)
            # We already parsed json, but _handle_response does it again.
            # It's cleaner to just pass the response object.

            # Note: _handle_response might update token.
            self._handle_response(response)

            # If we are here, it's a 200 OK
            return self._finalize_login(resp_json.get("data", {}))

        except httpx.RequestError as e:
            raise NetworkError(f"Login request failed: {e}")
        except MFARequiredError:
            raise  # Re-raise
        except Exception as e:
            # Catch-all to ensure we don't crash without info, but re-raise specific ones
            if isinstance(e, (ApiError, EcoleDirecteError)):
                raise
            raise LoginError(f"Login failed: {str(e)}")

    async def _get_qcm_connexion(self) -> Dict[str, Any]:
        url = "https://api.ecoledirecte.com/v3/connexion/doubleauth.awp"
        params = {"verbe": "get", "v": self.api_version}
        body = "data={}"

        response = await self.client.post(url, params=params, content=body)

        json_data = self._handle_response(response)
        return json_data.get("data", {})

    async def submit_mfa(self, answer: str) -> Union[Student, Family]:
        encoded_answer = base64.b64encode(answer.encode("utf-8")).decode("ascii")
        url = "https://api.ecoledirecte.com/v3/connexion/doubleauth.awp"
        params = {"verbe": "post", "v": self.api_version}
        body = f'data={{"choix": "{encoded_answer}"}}'

        response = await self.client.post(url, params=params, content=body)
        json_data = self._handle_response(response)

        data = json_data.get("data", {})
        cn = data.get("cn")
        cv = data.get("cv")

        if not cn or not cv:
            raise LoginError("MFA success but CN/CV missing")

        self.cn = cn
        self.cv = cv

        return await self._login_with_cn_cv(cn, cv)

    async def _login_with_cn_cv(self, cn, cv) -> Union[Student, Family]:
        await self._get_gtk()
        if not hasattr(self, "_temp_credentials"):
            raise LoginError("Credentials lost during MFA flow")

        username, password = self._temp_credentials
        encoded_user = self._encode_string(username)
        encoded_pass = self._encode_string(password)

        # Manual construction
        body = f'data={{"identifiant":"{encoded_user}", "motdepasse":"{encoded_pass}", "isRelogin": false, "cn":"{cn}", "cv":"{cv}", "uuid": "", "fa": [{{"cn": "{cn}", "cv": "{cv}"}}]}}'

        response = await self.client.post(
            url="https://api.ecoledirecte.com/v3/login.awp",
            params={"v": self.api_version},
            content=body,
        )
        json_data = self._handle_response(response)

        return self._finalize_login(json_data.get("data", {}))

    def _finalize_login(self, data: Dict[str, Any]) -> Union[Student, Family]:
        accounts_data = data.get("accounts", [])
        if not accounts_data:
            raise LoginError("No accounts found in login response")

        main_account_data = accounts_data[0]
        account_type = main_account_data.get("typeCompte")

        if account_type == "E":
            return Student(self, main_account_data.get("id"))
        elif account_type == "Famille" or account_type == "1":
            return Family(self, data)
        else:
            raise LoginError(f"Unknown account type: {account_type}")

    async def request(self, url: str, args: Dict[str, Any] = None) -> Dict[str, Any]:
        if args is None:
            args = {}

        payload = args.copy()
        if self.token:
            payload["token"] = self.token

        body = f"data={json.dumps(payload)}"

        try:
            response = await self.client.post(url, content=body)
            return self._handle_response(response)
        except httpx.RequestError as e:
            raise NetworkError(f"Request failed: {e}")

    async def close(self):
        await self.client.aclose()
