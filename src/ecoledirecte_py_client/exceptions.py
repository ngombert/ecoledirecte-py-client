class EcoleDirecteError(Exception):
    """Base exception for EcoleDirecte API"""

    pass


class LoginError(EcoleDirecteError):
    """Raised when authentication fails"""

    pass


class ApiError(EcoleDirecteError):
    """Raised when API returns a non-200 code or error message"""

    pass


class MFARequiredError(LoginError):
    """Raised when MFA (QCM) is required"""

    def __init__(self, message, question, propositions):
        super().__init__(message)
        self.question = question
        self.propositions = propositions
