import httpx
import json
import base64
import urllib.parse
from typing import Optional, Union, Dict, Any, Tuple
from .models import LoginResponse, Account
from .exceptions import LoginError, ApiError, MFARequiredError
from .student import Student
from .family import Family


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
            "Origin": "https://www.ecoledirecte.com",
            "Referer": "https://www.ecoledirecte.com/",
            "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
        }
        self.client = httpx.AsyncClient(headers=self.headers, verify=False)
        self.accounts: list[Account] = []
        self.api_version = "4.90.1"

    async def _get_gtk(self):
        """Retrieves the GTK (Global Token Key) and sets up session cookies."""
        url = "https://api.ecoledirecte.com/v3/login.awp"
        params = {"v": self.api_version, "gtk": "1"}

        # Reference implementation removes x-gtk header before requesting a new one
        if "x-gtk" in self.client.headers:
            del self.client.headers["x-gtk"]
        if "x-gtk" in self.headers:
            del self.headers["x-gtk"]

        try:
            # httpx automatically updates cookies in the client's cookie_jar
            response = await self.client.get(url, params=params)

            # Use .get() to access cookie by name safely
            gtk_value = response.cookies.get("GTK")
            if gtk_value:
                self.headers["x-gtk"] = gtk_value
                self.client.headers.update({"x-gtk": gtk_value})
                print(f"DEBUG: GTK found: {gtk_value}")
            else:
                print("DEBUG: GTK cookie not found in response")
                # Fallback: check if we already have it in the jar and just use that?
                # But ref implies we should get a new one.

        except Exception as e:
            print(f"DEBUG: Failed to get GTK: {e}")

    def _encode_string(self, string: str) -> str:
        """
        Custom encoding from reference implementation.
        """
        return (
            string.replace("%", "%25")
            .replace("&", "%26")
            .replace("+", "%2B")
            .replace("\\", "\\\\\\")
            .replace("\\\\", "\\\\\\\\")
            .replace('"', '\\"')  # JSON escape for manual construction
        )

    async def login(self, username, password) -> Union[Student, Family]:
        # Step 1: Get GTK
        await self._get_gtk()

        # Store credentials for potential MFA re-login
        self._temp_credentials = (username, password)

        url = "https://api.ecoledirecte.com/v3/login.awp"

        # Step 2: Construct payload manually as per reference (json.dumps might be fine but let's mimic ref exactly for safety)
        # Ref: data={"identifiant": ..., "motdepasse": ..., "isRelogin": false}

        encoded_user = self._encode_string(username)
        encoded_pass = self._encode_string(password)

        # Note: We construct the INNER JSON string first
        payload_dict = {
            "identifiant": username,  # We'll try standard json dumps first with the extras, if that fails we go full manual string
            "motdepasse": password,
            "isRelogin": False,
        }

        # Let's try standard JSON first but with the isRelogin field
        body = f"data={json.dumps(payload_dict, separators=(',', ':'))}"

        # If we wanted to use the manual encoding:
        # body = f'data={{"identifiant":"{encoded_user}", "motdepasse":"{encoded_pass}", "isRelogin": false}}'

        # Let's stick to json.dumps for now, but with updated headers and GTK.
        # Actually, let's use the manual construction to eliminate that variable since we have the code.
        body = f'data={{"identifiant":"{encoded_user}", "motdepasse":"{encoded_pass}", "isRelogin": false}}'

        print(f"DEBUG: POST {url}")
        print(f"DEBUG: Body: {body}")

        try:
            # Add API Version param
            response = await self.client.post(
                url, params={"v": self.api_version}, content=body
            )
            print(f"DEBUG: Status Code: {response.status_code}")

            # Capture token from headers immediately
            if "x-token" in response.headers:
                self.token = response.headers["x-token"]
                self.headers["x-token"] = self.token
                self.client.headers.update({"x-token": self.token})

            if response.status_code != 200:
                raise ApiError(f"HTTP Error: {response.status_code}")

            resp_json = response.json()
            code = resp_json.get("code")

            if code == 250:  # ED_MFA_REQUIRED
                print("DEBUG: MFA Required (Code 250)")
                # Fetch QCM Question
                qcm = await self._get_qcm_connexion()
                question = base64.b64decode(qcm.get("question", "")).decode("utf-8")
                propositions = [
                    base64.b64decode(p).decode("utf-8")
                    for p in qcm.get("propositions", [])
                ]

                # We raise a special exception that carries the MFA data
                # The caller should catch this, ask the user, and then call submit_mfa
                raise MFARequiredError(
                    "MFA Required", question=question, propositions=propositions
                )

            elif code == 505:
                print(
                    f"DEBUG: Invalid Credentials or Session Invalid. Code: 505. Data: {resp_json.get('data')}"
                )
                raise LoginError("Valid credentials required")
            elif code != 200:
                raise ApiError(
                    f"API Error code: {code}, message: {resp_json.get('message')}"
                )

            # Parse success
            self.token = resp_json.get("token") or self.token

            # If still no token, we might have an issue, but usually it's in header or body

            return self._finalize_login(resp_json.get("data", {}))

        except httpx.RequestError as e:
            raise ApiError(f"Request failed: {e}")

    async def _get_qcm_connexion(self) -> Dict[str, Any]:
        url = "https://api.ecoledirecte.com/v3/connexion/doubleauth.awp"
        params = {"verbe": "get", "v": self.api_version}
        body = "data={}"
        response = await self.client.post(url, params=params, content=body)
        resp_json = response.json()
        if resp_json.get("code") != 200:
            raise ApiError(f"Failed to get MFA QCM: {resp_json}")

        # Update token if present (Ref does this)
        if "x-token" in response.headers:
            self.token = response.headers["x-token"]
            self.headers["x-token"] = self.token
            self.client.headers.update({"x-token": self.token})

        return resp_json.get("data", {})

    async def submit_mfa(self, answer: str) -> Union[Student, Family]:
        """
        Submits the MFA answer (base64 encoded in the implementation).
        Answer provided here should be the plain text answer chosen by user.
        """
        # We need to find the base64 encoded proposition that matches the answer
        # But wait, looking at ref:
        # data={"choix": "BASE64_STRING"}

        # We assume the user gives us the decoded string (e.g. "Paris").
        # We need to encode it back to base64?
        # Ref logic:
        # response = base64.b64encode(bytes(self.qcm_json[question][0], "utf-8")).decode("ascii")
        # Then post data={"choix": response}

        encoded_answer = base64.b64encode(answer.encode("utf-8")).decode("ascii")

        url = "https://api.ecoledirecte.com/v3/connexion/doubleauth.awp"
        params = {"verbe": "post", "v": self.api_version}
        body = f'data={{"choix": "{encoded_answer}"}}'

        response = await self.client.post(url, params=params, content=body)
        resp_json = response.json()

        if resp_json.get("code") != 200:
            raise ApiError(f"MFA Failed: {resp_json}")

        # Get CN and CV from response to finalize login
        data = resp_json.get("data", {})
        cn = data.get("cn")
        cv = data.get("cv")

        if not cn or not cv:
            raise ApiError("MFA success but CN/CV missing")

        # Now we need to RE-LOGIN with CN/CV
        return await self._login_with_cn_cv(cn, cv)

    async def _login_with_cn_cv(self, cn, cv) -> Union[Student, Family]:
        await self._get_gtk()
        url = "https://api.ecoledirecte.com/v3/login.awp"

        # We need the username/password again.
        # Ideally we should have stored them or passed them.
        # For now, let's assume we can't easily get them unless stored in class.
        # Let's prompt or error.
        # BETTER: Store username/password in self during first login attempt?
        # Or Just raise Validation error if they are missing.
        # Actually, let's store them in `self._temp_credentials` during login.

        if not hasattr(self, "_temp_credentials"):
            raise ApiError("Credentials lost during MFA flow")

        username, password = self._temp_credentials
        encoded_user = self._encode_string(username)
        encoded_pass = self._encode_string(password)

        payload_dict = {
            "identifiant": username,
            "motdepasse": password,
            "isRelogin": False,
            "cn": cn,
            "cv": cv,
            "uuid": "",
            "fa": [{"cn": cn, "cv": cv}],
        }

        # Manual construction heavily preferred for this sensitive endpoint
        body = f'data={{"identifiant":"{encoded_user}", "motdepasse":"{encoded_pass}", "isRelogin": false, "cn":"{cn}", "cv":"{cv}", "uuid": "", "fa": [{{"cn": "{cn}", "cv": "{cv}"}}]}}'

        response = await self.client.post(
            url, params={"v": self.api_version}, content=body
        )
        resp_json = response.json()

        if resp_json.get("code") != 200:
            raise ApiError(f"Login with MFA failed: {resp_json}")

        self.token = resp_json.get("token")
        if self.token:
            self.headers["x-token"] = self.token
            self.client.headers.update({"x-token": self.token})

        return self._finalize_login(resp_json.get("data", {}))

    def _finalize_login(self, data: Dict[str, Any]) -> Union[Student, Family]:
        accounts_data = data.get("accounts", [])
        if not accounts_data:
            raise ApiError("No accounts found")

        main_account_data = accounts_data[0]
        account_type = main_account_data.get("typeCompte")

        if account_type == "E":
            return Student(self, main_account_data.get("id"))
        elif account_type == "Famille" or account_type == "1":
            family = Family(self, data)
            return family
        else:
            raise ApiError(f"Unknown account type: {account_type}")

    async def request(self, url: str, args: Dict[str, Any] = None) -> Dict[str, Any]:
        if args is None:
            args = {}

        # JS logic:
        # data = JSON.stringify({ ...args, token: this.token })
        # post url, `data=${data}`

        payload = args.copy()
        if self.token:
            payload["token"] = self.token

        body = f"data={json.dumps(payload)}"

        try:
            response = await self.client.post(url, content=body)
            if response.status_code != 200:
                raise ApiError(f"HTTP Error: {response.status_code}")

            resp_json = response.json()
            # Basic error check
            if resp_json.get("code") != 200:
                raise ApiError(
                    f"API Error code: {resp_json.get('code')}, message: {resp_json.get('message')}"
                )

            return resp_json

        except httpx.RequestError as e:
            raise ApiError(f"Request failed: {e}")

    async def close(self):
        await self.client.aclose()
