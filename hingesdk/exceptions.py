import traceback
from typing import Optional, Dict, Any


class HingeAPIError(Exception):
    """Base exception for Hinge API errors"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        self.traceback = traceback.format_exc()
        super().__init__(self.__str__())

    def __str__(self) -> str:
        error_msg = [f"Hinge API Error: {self.message}"]
        if self.details:
            error_msg.append("Details:")
            for key, value in self.details.items():
                error_msg.append(f"  {key}: {value}")
        error_msg.append("\nTraceback:")
        error_msg.append(self.traceback)
        return "\n".join(error_msg)


class HingeAuthError(HingeAPIError):
    """Raised when authentication fails"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(f"Authentication Error: {message}", details)


class HingeRequestError(HingeAPIError):
    """Raised when a request fails"""

    def __init__(
        self, status_code: int, message: str, response_body: Optional[str] = None
    ):
        details = {
            "status_code": status_code,
            "response_body": response_body or "No response body",
            "endpoint": None,  # Will be set by the client
            "request_headers": None,  # Will be set by the client
            "request_body": None,  # Will be set by the client
        }
        super().__init__(f"Request Error: {message}", details)
