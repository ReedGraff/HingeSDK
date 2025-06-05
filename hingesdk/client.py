import uuid
import logging
import requests
from typing import Optional
from .exceptions import HingeAPIError, HingeAuthError, HingeRequestError


class HingeClient:
    """Base client for Hinge API interactions"""

    BASE_URL = "https://prod-api.hingeaws.net"
    MEDIA_URL = "https://media.hingenexus.com"

    def __init__(
        self,
        auth_token: Optional[str] = None,
        app_version: str = "9.75.0",
        os_version: str = "14",
        device_model: str = "Pixel 6a",
        install_id: str = "735de715-0876-45c5-be1e-aecdf8cb42d1",
        device_id: str = "b4b578b8250e8ca8",
        accept_language: str = "en-US",
        device_region: str = "US",
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        """
        Initialize Hinge client with authentication and device details.

        Args:
            auth_token: Bearer token for authentication
            app_version: Application version
            os_version: Operating system version
            device_model: Device model name
            install_id: Installation identifier
            device_id: Device identifier
            user_id: User identifier. AKA player_id (optional)
            session_id: Session identifier (optional)
        """
        self.logger = logging.getLogger(__name__)

        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        self.session = requests.Session()
        self.auth_token = auth_token
        self.session_id = session_id
        self.user_id = user_id

        self.default_headers = {
            "x-app-version": app_version,
            "x-os-version": os_version,
            "x-os-version-code": "34",
            "x-device-model": device_model,
            "x-device-model-code": device_model,
            "x-device-manufacturer": "Google",
            "x-build-number": "168200482",
            "x-device-platform": "android",
            "x-install-id": install_id,
            "x-device-id": device_id,
            "accept-language": accept_language,
            "x-device-region": device_region,
            "host": "prod-api.hingeaws.net",
            "connection": "Keep-Alive",
            "accept-encoding": "gzip",
            "user-agent": "okhttp/4.12.0",
        }

        if auth_token:
            self.default_headers["authorization"] = f"Bearer {auth_token}"
        if session_id:
            self.default_headers["x-session-id"] = session_id

        self.logger.debug("Initialized HingeClient with device ID: %s", device_id)

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Internal request handler with error checking"""
        headers = kwargs.get("headers", {}).copy()
        headers.update(self.default_headers)
        kwargs["headers"] = headers

        self.logger.debug("Sending %s request to URL: %s", method, url)
        self.logger.debug("Request headers: %s", headers)
        self.logger.debug("Request body: %s", kwargs.get("json") or kwargs.get("data"))

        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            self.logger.debug("Response status: %s", response.status_code)
            return response
        except requests.exceptions.HTTPError as e:
            self.logger.error("HTTP error occurred: %s", str(e))
            error = HingeRequestError(
                status_code=e.response.status_code,
                message=str(e),
                response_body=e.response.text,
            )
            error.details["endpoint"] = url
            error.details["request_headers"] = {
                k: v
                for k, v in kwargs["headers"].items()
                if k.lower() != "authorization"
            }
            error.details["request_body"] = kwargs.get("json") or kwargs.get("data")

            if e.response.status_code == 401:
                raise HingeAuthError("Authentication failed", error.details)
            if e.response.status_code == 412:
                raise HingeAuthError("Precondition failed", error.details)
            raise error
        except requests.exceptions.RequestException as e:
            self.logger.exception("Non-HTTP request error occurred")
            raise HingeAPIError(
                f"Request failed: {str(e)}",
                {"exception_type": type(e).__name__, "url": url, "method": method},
            )

    @classmethod
    def login_with_sms(
        cls, phone_number: str, device_id: str, install_id: str
    ) -> "HingeClient":
        """
        Perform SMS login and return an authenticated client instance.

        Args:
            phone_number: Phone number in international format (e.g., "+12345678901")
            device_id: Unique device identifier
            install_id: Installation identifier

        Returns:
            HingeClient: Authenticated client instance

        Raises:
            HingeAPIError: If the login process fails
        """
        logger = logging.getLogger(f"{__name__}")
        logger.setLevel(logging.DEBUG)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        logger.info("Starting SMS login for phone: %s", phone_number)

        temp_client = cls(device_id=device_id, install_id=install_id)

        initiate_url = f"{cls.BASE_URL}/auth/sms/v2/initiate"
        payload = {"phoneNumber": phone_number, "deviceId": device_id}
        headers = {"content-type": "application/json; charset=UTF-8"}

        response = temp_client._request(
            "POST", initiate_url, json=payload, headers=headers
        )
        logger.info("SMS initiation response code: %d", response.status_code)
        logger.debug("SMS initiation response text: '%s'", response.text)

        sms_code = input("Enter the SMS code received: ")

        verify_url = f"{cls.BASE_URL}/auth/sms/v2"
        verify_payload = {
            "deviceId": device_id,
            "installId": install_id,
            "phoneNumber": phone_number,
            "otp": sms_code,
        }

        verify_response = temp_client._request(
            "POST", verify_url, json=verify_payload, headers=headers
        )

        try:
            verify_data = verify_response.json()
        except requests.exceptions.JSONDecodeError:
            logger.error("Failed to parse verification response")
            raise HingeAPIError(
                "Failed to parse verification response",
                {
                    "status_code": verify_response.status_code,
                    "response_text": verify_response.text,
                },
            )

        if verify_response.status_code == 412 and "caseId" in verify_data:
            logger.warning(
                "Email verification required, case ID: %s", verify_data.get("caseId")
            )
            raise HingeAuthError(
                "Email verification required",
                {
                    "case_id": verify_data.get("caseId"),
                    "message": verify_data.get("message"),
                },
            )

        auth_token = verify_data.get("token")
        user_id = verify_data.get("playerId")
        session_id = verify_data.get("sessionId")

        logger.info("Verification successful. Token and session retrieved.")
        logger.debug("Auth Token: %s", auth_token)
        logger.debug("User ID: %s", user_id)
        logger.debug("Session ID: %s", session_id)

        if not auth_token:
            logger.error("No auth token received.")
            raise HingeAPIError(
                "Failed to retrieve authentication token", {"response": verify_data}
            )

        if not session_id:
            session_id = str(uuid.uuid4())
            logger.warning(
                "No session ID received; generated fallback session ID: %s", session_id
            )

        return cls(
            auth_token=auth_token,
            device_id=device_id,
            install_id=install_id,
            user_id=user_id,
            session_id=session_id,
        )
