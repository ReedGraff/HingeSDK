import datetime
from typing import List, Dict, Optional
import uuid
from .client import HingeClient

class HingeAPIClient(HingeClient):
    """Client for Hinge API operations"""
    
    def like_profile(self,
        subject_id: str,
        rating_token: str,
        comment: Optional[str] = None,
        photo: Optional[Dict] = None,
        prompt: Optional[Dict] = None,
        initiated_with: str = "standard",
        origin: str = "compatibles",
        has_pairing: bool = False) -> Dict:
        """
        Like a profile with an optional comment, photo, or prompt response.
        
        Args:
            subject_id: ID of the profile to like
            rating_token: JWT token for rating authentication
            comment: Optional comment to include with the like
            photo: Optional photo metadata to include
            prompt: Optional prompt response to include
            initiated_with: Type of like ("standard" or "superlike")
            origin: Source of the rating (default: "compatibles")
            has_pairing: Whether this creates a pairing (default: False)
            
        Returns:
            Dict: JSON response from the API
            
        Raises:
            HingeAPIError: If the request fails
            HingeAuthError: If authentication fails
        """
        url = f"{self.BASE_URL}/rate/v2/initiate"
        
        # Generate unique rating ID
        rating_id = str(uuid.uuid4())
        
        # Base payload structure
        payload = {
            "ratingId": rating_id,
            "ratingToken": rating_token,
            "subjectId": subject_id,
            "sessionId": self.session_id,
            "rating": "note",
            "origin": origin,
            "hasPairing": has_pairing,
            "created": datetime.datetime.utcnow().isoformat() + "Z",
            "initiatedWith": initiated_with
        }
        
        # Add content if provided
        content = {}
        if comment:
            content["comment"] = comment
        if photo:
            content["photo"] = photo
        if prompt:
            content["prompt"] = prompt
        
        if content:
            payload["content"] = content
        
        headers = {
            "content-type": "application/json; charset=UTF-8"
        }
        
        response = self._request("POST", url, json=payload, headers=headers)
        return response.json()

    def send_message(self,
        subject_id: str,
        message: str,
        match_message: bool = False,
        origin: str = "Native Chat",
        message_type: str = "message",
        ays: bool = True) -> Dict:
        """
        Send a message to another user.
        
        Args:
            subject_id: The ID of the user/conversation to send the message to
            message: The message content to send
            match_message: Whether this is a match message (default: False)
            origin: Origin of the message (default: "Native Chat")
            message_type: Type of message (default: "message")
            ays: Are You Sure flag (default: True)
            
        Returns:
            Dict: JSON response from the API
            
        Raises:
            HingeAPIError: If the request fails
            HingeAuthError: If authentication fails
        """
        url = f"{self.BASE_URL}/message/send"
        
        # Generate a unique dedupId for each message
        dedup_id = str(uuid.uuid4())
        
        payload = {
            "subjectId": subject_id,
            "matchMessage": match_message,
            "origin": origin,
            "dedupId": dedup_id,
            "messageData": {
                "message": message
            },
            "messageType": message_type,
            "ays": ays
        }
        
        # Add content-type header specifically for this endpoint
        headers = {
            "content-type": "application/json; charset=UTF-8"
        }
        
        response = self._request("POST", url, json=payload, headers=headers)
        return response.json()

    def get_standouts(self, additional_headers: Optional[Dict] = None) -> Dict:
        """
        Get standout profiles from Hinge.
        
        Args:
            additional_headers: Optional additional headers to include in the request
            
        Returns:
            Dict: JSON response containing standout profiles data including:
                - status: Validation status
                - expiration: When the standouts expire
                - free: List of free standout profiles
                - paid: List of paid standout profiles
                
        Raises:
            HingeAPIError: If the request fails
            HingeAuthError: If authentication fails
        """
        url = f"{self.BASE_URL}/standouts/v2"
        
        # Prepare headers
        headers = {}
        if additional_headers:
            headers.update(additional_headers)
        
        response = self._request("GET", url, headers=headers)
        return response.json()

    def get_recommendations(self, 
        active_today: bool = False,
        new_here: bool = False,
        additional_headers: Optional[Dict] = None) -> Dict:
        """
        Get user recommendations from Hinge.
        
        Args:
            player_id: The player/user ID to get recommendations for
            active_today: Whether the user was active today (default: False)
            new_here: Whether the user is new (default: False)
            additional_headers: Optional additional headers to include
            
        Returns:
            Dict: JSON response containing recommendation data (including user IDs and rating tokens)
        """
        url = f"{self.BASE_URL}/rec/v2"
        payload = {
            "playerId": self.user_id,
            "activeToday": active_today,
            "newHere": new_here
        }
        response = self._request("POST",url,json=payload)
        return response.json()
    
    def get_public_users(self, user_ids: List[str]) -> Dict:
        """
        Get public user profiles.
        
        Args:
            user_ids: List of user IDs to fetch
            
        Returns:
            Dict: JSON response containing user data
        """
        url = f"{self.BASE_URL}/user/v2/public"
        params = {"ids": ",".join(user_ids)}
        response = self._request("GET", url, params=params)
        return response.json()
    
    def get_public_content(self, content_ids: List[str]) -> Dict:
        """
        Get public content.
        
        Args:
            content_ids: List of content IDs to fetch
            
        Returns:
            Dict: JSON response containing content data
        """
        url = f"{self.BASE_URL}/content/v1/public"
        params = {"ids": ",".join(content_ids)}
        response = self._request("GET", url, params=params)
        return response.json()
    
    def get_settings(self) -> Dict:
        """Get user settings"""
        url = f"{self.BASE_URL}/content/v1/settings"
        response = self._request("GET", url)
        return response.json()
    
    def get_auth_settings(self) -> Dict:
        """Get authentication settings"""
        url = f"{self.BASE_URL}/auth/settings"
        response = self._request("GET", url)
        return response.json()
    
    def get_notification_settings(self) -> Dict:
        """Get notification settings"""
        url = f"{self.BASE_URL}/notification/v1/settings"
        response = self._request("GET", url)
        return response.json()
    
    def get_like_limit(self) -> Dict:
        """Get like limit information"""
        url = f"{self.BASE_URL}/likelimit"
        response = self._request("GET", url)
        return response.json()
    
    def get_user_traits(self) -> Dict:
        """Get user traits"""
        url = f"{self.BASE_URL}/user/v2/traits"
        response = self._request("GET", url)
        return response.json()
    
    def get_account_info(self) -> Dict:
        """Get account information"""
        url = f"{self.BASE_URL}/store/v2/account"
        response = self._request("GET", url)
        return response.json()
    
    def get_export_status(self) -> Dict:
        """Get data export status"""
        url = f"{self.BASE_URL}/user/export/status"
        response = self._request("GET", url)
        return response.json()