import uuid
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

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Internal request handler with error checking"""
        headers = kwargs.get("headers", {}).copy()
        headers.update(self.default_headers)
        kwargs["headers"] = headers

        print(f"Request: {method} {url}")
        print(f"Headers: {headers}")
        print(f"Body: {kwargs.get('json') or kwargs.get('data')}")

        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as e:
            error = HingeRequestError(
                status_code=e.response.status_code,
                message=str(e),
                response_body=e.response.text,
            )
            # Add additional context to the error
            error.details["endpoint"] = url
            error.details["request_headers"] = {
                k: v
                for k, v in kwargs["headers"].items()
                if k.lower() not in ["authorization"]
            }
            error.details["request_body"] = kwargs.get("json") or kwargs.get("data")

            if e.response.status_code == 401:
                raise HingeAuthError("Authentication failed", error.details)
            if e.response.status_code == 412:
                raise HingeAuthError("Precondition failed", error.details)
            raise error
        except requests.exceptions.RequestException as e:
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
        # Create temporary client for authentication
        temp_client = cls(device_id=device_id, install_id=install_id)

        # Step 1: Initiate SMS authentication
        initiate_url = f"{cls.BASE_URL}/auth/sms/v2/initiate"
        payload = {"phoneNumber": phone_number, "deviceId": device_id}
        headers = {"content-type": "application/json; charset=UTF-8"}

        response = temp_client._request(
            "POST", initiate_url, json=payload, headers=headers
        )
        print(f"Initiate response status: {response.status_code}")
        print(f"Initiate response text: '{response.text}'")

        # Since response is empty (likely 204 No Content), we don’t expect a verificationId
        # Proceed directly to verification assuming the SMS code is sufficient

        # Step 2: Prompt user for SMS code
        sms_code = input("Enter the SMS code received: ")

        # Step 3: Verify SMS code
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
            raise HingeAPIError(
                "Failed to parse verification response",
                {
                    "status_code": verify_response.status_code,
                    "response_text": verify_response.text,
                },
            )
        # Check if response need extra email verification
        if verify_data.status_code == 412 and "caseId" in verify_data.json():
            raise HingeAuthError(
                "Email verification required",
                {
                    "case_id": verify_data.get("caseId"),
                    "message": verify_data.get("message"),
                },
            )

        # Extract bearer token and other details
        auth_token = verify_data.get("token")
        user_id = verify_data.get("playerId")
        session_id = verify_data.get("sessionId")

        print(f"Verification response: {verify_data}")
        print(f"Token: {auth_token}")
        print(f"User ID: {user_id}")
        print(f"Session ID: {session_id}")

        if not auth_token:
            raise HingeAPIError(
                "Failed to retrieve authentication token", {"response": verify_data}
            )

        if not session_id:
            session_id = str(uuid.uuid4())
            print(f"Generated Session ID: {session_id}")

        # Return fully authenticated client
        return cls(
            auth_token=auth_token,
            device_id=device_id,
            install_id=install_id,
            user_id=user_id,
            session_id=session_id,
        )
