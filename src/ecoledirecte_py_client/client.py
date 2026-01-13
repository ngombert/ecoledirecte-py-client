import httpx
import json
import base64
import os
from typing import Optional, Union, Dict, Any, Callable, List
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
from .managers.homework_manager import HomeworkManager
from .managers.schedule_manager import ScheduleManager
from .managers.messages_manager import MessagesManager


class Client:
    def __init__(
        self,
        device_file: Optional[str] = "device.json",
        qcm_file: Optional[str] = "qcm.json",
        mfa_callback: Optional[Callable[[str, List[str]], str]] = None,
    ):
        """
        Initialize EcoleDirecte client.

        Args:
            device_file: Path to device token cache file (None to disable persistence)
            qcm_file: Path to MFA answer cache file (None to disable persistence)
            mfa_callback: Optional callback function for interactive MFA.
                         Signature: (question: str, options: List[str]) -> str
                         If None and MFA required, raises MFARequiredError
        """
        self.token: Optional[str] = None
        self.device_file = device_file
        self.qcm_file = qcm_file
        self.mfa_callback = mfa_callback

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
        self.homework = HomeworkManager(self)
        self.schedule = ScheduleManager(self)
        self.messages = MessagesManager(self)
        self.cn: Optional[str] = None
        self.cv: Optional[str] = None

    # =========================================================================
    # Persistence Helper Methods
    # =========================================================================

    def _load_device_tokens(self) -> tuple[Optional[str], Optional[str]]:
        """Load device tokens (cn, cv) from file if persistence is enabled."""
        if not self.device_file or not os.path.exists(self.device_file):
            return None, None

        try:
            with open(self.device_file, "r") as f:
                data = json.load(f)
                return data.get("cn"), data.get("cv")
        except Exception:
            # Silently ignore errors (corrupted file, permissions, etc.)
            return None, None

    def _save_device_tokens(self, cn: str, cv: str):
        """Save device tokens to file if persistence is enabled."""
        if not self.device_file:
            return

        try:
            with open(self.device_file, "w") as f:
                json.dump({"cn": cn, "cv": cv}, f, indent=2)
        except Exception:
            # Silently ignore errors
            pass

    def _load_qcm_cache(self) -> dict:
        """Load saved MFA answers from file if persistence is enabled."""
        if not self.qcm_file or not os.path.exists(self.qcm_file):
            return {}

        try:
            with open(self.qcm_file, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_qcm_answer(self, question: str, answer: str):
        """Save a successful MFA answer to file if persistence is enabled."""
        if not self.qcm_file:
            return

        try:
            data = self._load_qcm_cache()
            if question not in data:
                data[question] = []

            if answer not in data[question]:
                data[question].append(answer)

            with open(self.qcm_file, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            # Silently ignore errors
            pass

    # =========================================================================
    # Authentication Methods
    # =========================================================================

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

            if response.status_code != 200:
                self._handle_response(response)

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
            raise LoginError(f"Invalid Credentials or Session: {message}", code=code)
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
        """
        Authenticate with EcoleDirecte.

        Args:
            username: EcoleDirecte username
            password: EcoleDirecte password
            cn: Optional device token (auto-loaded from file if available)
            cv: Optional device token (auto-loaded from file if available)

        Returns:
            Student or Family account instance

        Raises:
            MFARequiredError: If MFA is required and no callback is configured
            LoginError: If authentication fails
        """
        await self._get_gtk()
        self._temp_credentials = (username, password)

        # Auto-load device tokens if not provided
        if cn is None and cv is None:
            cn, cv = self._load_device_tokens()

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
            if not self.token and "token" in resp_json:
                self._update_token(resp_json["token"])

            code = resp_json.get("code")

            if code == 250:
                # MFA Required - Try auto-submit or invoke callback
                return await self._handle_mfa_flow()

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

    async def _handle_mfa_flow(self) -> Union[Student, Family]:
        """
        Handle MFA authentication flow with auto-submit and callback support.

        Process:
        1. Fetch QCM question and options
        2. Try auto-submit from cached answers
        3. If auto-submit fails and callback provided, invoke callback
        4. If no callback, raise MFARequiredError (backward compatible)
        5. On success, save answer to cache and device tokens

        Returns:
            Student or Family account instance

        Raises:
            MFARequiredError: If MFA required and no callback configured
            LoginError: If MFA verification fails
        """
        # Fetch QCM question
        qcm = await self._get_qcm_connexion()
        question = base64.b64decode(qcm.get("question", "")).decode("utf-8")
        propositions = [
            base64.b64decode(p).decode("utf-8") for p in qcm.get("propositions", [])
        ]

        # Try auto-submit from cache
        cached_answers = self._load_qcm_cache().get(question, [])
        if cached_answers:
            # Try most recent answer
            cached_answer = cached_answers[-1]
            try:
                session = await self._submit_mfa_answer(cached_answer, question)
                return session
            except Exception:
                # Auto-submit failed, continue to callback or raise
                pass

        # No cached answer or auto-submit failed
        if self.mfa_callback is None:
            # Backward compatible: raise error for manual handling
            raise MFARequiredError(
                "MFA Required", question=question, propositions=propositions
            )

        # Invoke callback for interactive MFA
        try:
            answer = self.mfa_callback(question, propositions)
            if not answer or not isinstance(answer, str):
                raise ValueError("MFA callback must return a non-empty string")

            session = await self._submit_mfa_answer(answer, question)
            return session

        except Exception as e:
            if isinstance(e, (ApiError, EcoleDirecteError)):
                raise
            raise LoginError(f"MFA callback failed: {str(e)}")

    async def _submit_mfa_answer(
        self, answer: str, question: str
    ) -> Union[Student, Family]:
        """
        Submit MFA answer and complete authentication.

        On success, saves the answer to cache and device tokens to file.

        Args:
            answer: The MFA answer to submit
            question: The MFA question (for caching)

        Returns:
            Student or Family account instance

        Raises:
            ApiError: If submission fails
        """
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

        # Save successful answer to cache
        self._save_qcm_answer(question, answer)

        # Save device tokens
        self._save_device_tokens(cn, cv)

        return await self._login_with_cn_cv(cn, cv)

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
