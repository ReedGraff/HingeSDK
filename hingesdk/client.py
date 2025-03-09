import requests
from typing import Dict, Optional
from .exceptions import HingeAPIError, HingeAuthError, HingeRequestError

class HingeClient:
    """Base client for Hinge API interactions"""
    
    BASE_URL = "https://prod-api.hingeaws.net"
    MEDIA_URL = "https://media.hingenexus.com"
    
    def __init__(self, 
                 auth_token: str,
                 app_version: str = "9.68.0",
                 os_version: str = "14",
                 device_model: str = "Pixel 6a",
                 install_id: str = "735de715-0876-45c5-be1e-aecdf8cb42d1",
                 device_id: str = "b4b578b8250e8ca8",
                 user_id: Optional[str] = None,
                 session_id: Optional[str] = None):
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
            "authorization": f"Bearer {auth_token}",
            "accept-language": "en-US",
            "x-device-region": "US",
            "host": "prod-api.hingeaws.net",
            "connection": "Keep-Alive",
            "accept-encoding": "gzip",
            "user-agent": "okhttp/4.12.0"
        }
        
        if session_id:
            self.default_headers["x-session-id"] = session_id

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Internal request handler with error checking"""
        headers = kwargs.get("headers", {})
        headers.update(self.default_headers)
        kwargs["headers"] = headers
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as e:
            error = HingeRequestError(
                status_code=e.response.status_code,
                message=str(e),
                response_body=e.response.text
            )
            # Add additional context to the error
            error.details['endpoint'] = url
            error.details['request_headers'] = {
                k: v for k, v in kwargs['headers'].items() 
                if k.lower() not in ['authorization']
            }
            error.details['request_body'] = kwargs.get('json') or kwargs.get('data')
            
            if e.response.status_code == 401:
                raise HingeAuthError("Authentication failed", error.details)
            raise error
        except requests.exceptions.RequestException as e:
            raise HingeAPIError(f"Request failed: {str(e)}", {
                'exception_type': type(e).__name__,
                'url': url,
                'method': method
            })
