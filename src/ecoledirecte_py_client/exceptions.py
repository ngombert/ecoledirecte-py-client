class EcoleDirecteError(Exception):
    """Base exception for all EcoleDirecte API errors."""

    pass


class NetworkError(EcoleDirecteError):
    """Raised when there is a network-related error (e.g., DNS, timeout)."""

    pass


class ApiError(EcoleDirecteError):
    """Raised when the API returns an error response (non-200 code or specific API error code)."""

    def __init__(self, message: str, code: int = 0):
        super().__init__(message)
        self.code = code


class AuthenticationError(ApiError):
    """Raised when authentication fails (HTTP 401/403 or API-specific auth errors)."""

    pass


class LoginError(AuthenticationError):
    """Raised when the login process specifically fails."""

    pass


class MFARequiredError(LoginError):
    """Raised when Multi-Factor Authentication is required."""

    def __init__(self, message: str, question: str, propositions: list[str]):
        super().__init__(message)
        self.question = question
        self.propositions = propositions


class ResourceNotFoundError(ApiError):
    """Raised when a requested resource is not found (HTTP 404)."""

    pass


class ServerError(ApiError):
    """Raised when the server encounters an internal error (HTTP 500+)."""

    pass
