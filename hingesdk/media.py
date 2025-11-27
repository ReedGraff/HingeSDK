from typing import Dict, Optional
from .client import HingeClient


class HingeMediaClient(HingeClient):
    """Client for handling Hinge media operations"""

    DEFAULT_MEDIA_HEADERS = {
        "host": "media.hingenexus.com",
        "connection": "Keep-Alive",
        "accept-encoding": "gzip",
        "user-agent": "okhttp/4.12.0",
    }

    def get_image(
        self,
        image_path: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
    ) -> bytes:
        """
        Retrieve an image from Hinge media server.

        Args:
            image_path: Path to the image (e.g., "image/upload/...")
            params: Optional query parameters
            headers: Optional additional headers

        Returns:
            bytes: Image content
        """
        url = f"{self.MEDIA_URL}/{image_path}"
        request_headers = self.DEFAULT_MEDIA_HEADERS.copy()

        if headers:
            request_headers.update(headers)

        response = self._request("GET", url, params=params, headers=request_headers)
        return response.content

    def get_processed_image(
        self,
        image_id: str,
        x: float = 0.0,
        y: float = 0.0,
        width: float = 1.0,
        height: float = 1.0,
        output_width: int = 864,
        quality: str = "auto",
        format: str = "webp",
    ) -> bytes:
        """
        Get a processed image with specified crop and resize parameters.

        Args:
            image_id: Image identifier
            x: Crop x position
            y: Crop y position
            width: Crop width
            height: Crop height
            output_width: Output width in pixels
            quality: Image quality setting
            format: Output format

        Returns:
            bytes: Processed image content
        """
        path = f"image/upload/x_{x:.2f},y_{y:.2f},w_{width:.2f},h_{height:.2f},c_crop/w_{output_width},q_{quality}/f_{format}/{image_id}"
        return self.get_image(path)
