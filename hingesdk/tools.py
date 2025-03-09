import os
import json
from typing import Dict, List, Optional
from .api import HingeAPIClient
from .media import HingeMediaClient
from .exceptions import HingeAPIError
import logging

class HingeTools:
    """Tools for extended Hinge API operations"""
    
    def __init__(self, 
                 api_client: HingeAPIClient,
                 media_client: HingeMediaClient):
        """
        Initialize HingeTools with API and media clients.
        
        Args:
            api_client: Initialized HingeAPIClient instance
            media_client: Initialized HingeMediaClient instance
        """
        self.api_client = api_client
        self.media_client = media_client
        self.logger = logging.getLogger(__name__)

    def download_recommendation_content(self,
        active_today: bool = False,
        new_here: bool = False,
        output_path: str = "output") -> Dict:
        """
        Get recommendations, fetch user content, and download all images.
        
        Args:
            active_today: Filter for active today users
            new_here: Filter for new users
            output_path: Output path for downloaded images
            
        Returns:
            Dict: Combined data including recommendations and user profiles
        """
        try:
            # Create base download path
            os.makedirs(os.path.join(os.getcwd(), output_path), exist_ok=True)

            # Step 1: Get recommendations
            self.logger.info("Fetching recommendations...")
            recommendations = self.api_client.get_recommendations(
                active_today=active_today,
                new_here=new_here
            )
            
            # Step 2: Extract user IDs from recommendations
            user_ids = []
            for feed in recommendations.get("feeds", []):
                for subject in feed.get("subjects", []):
                    user_ids.append(subject["subjectId"])
            
            if not user_ids:
                self.logger.warning("No user IDs found in recommendations")
                return {"recommendations": recommendations, "profiles": []}
            
            # Step 3: Get public user profiles
            self.logger.info(f"Fetching profiles for {len(user_ids)} users...")
            profiles = self.api_client.get_public_users(user_ids)
            
            # Step 4: Download images for each user
            for profile in profiles:
                user_id = profile["identityId"]
                self._download_user_images(user_id, profile.get("profile", {}), output_path=output_path)
            
            return {
                "recommendations": recommendations,
                "profiles": profiles
            }
            
        except HingeAPIError as e:
            self.logger.error(f"API error occurred: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error occurred: {str(e)}")
            raise

    def _download_user_images(self, user_id: str, profile: Dict, output_path: str) -> None:
        """
        Download all images for a user into a user-specific folder.
        
        Args:
            user_id: User ID for folder naming
            profile: User profile containing photo information
            output_path: Output path for downloaded images
        """
        user_folder = os.path.join(os.getcwd(), output_path, user_id)
        os.makedirs(user_folder, exist_ok=True)
        
        photos = profile.get("photos", [])
        if not photos:
            self.logger.warning(f"No photos found for user {user_id}")
            return
            
        self.logger.info(f"Downloading {len(photos)} images for user {user_id}...")
        
        for idx, photo in enumerate(photos):
            cdn_id = photo.get("cdnId")
            if not cdn_id:
                self.logger.warning(f"Photo {idx} for user {user_id} has no cdnId")
                continue
                
            try:
                # Get image extension from URL
                url = photo.get("url", "")
                ext = os.path.splitext(url)[1] or ".jpg"
                
                # Download base image (not cropped)
                image_data = self.media_client.get_image(f"image/upload/{cdn_id}{ext}")
                
                # Save image
                image_path = os.path.join(user_folder, f"photo_{idx}{ext}")
                with open(image_path, "wb") as f:
                    f.write(image_data)
                self.logger.debug(f"Saved image: {image_path}")
                
            except Exception as e:
                self.logger.error(f"Failed to download image {cdn_id} for user {user_id}: {str(e)}")

    def create_profile_json(self,
        active_today: bool = False,
        new_here: bool = False,
        output_file: str = "hinge_profiles.json") -> None:
        """
        Create a JSON file with user profiles from recommendations using question mappings.
        
        Args:
            active_today: Filter for active today users
            new_here: Filter for new users
            output_file: Path to save the JSON file
        """
        try:
            # Load question mappings
            mapping_path = os.path.join(os.path.dirname(__file__), "assets/prompts.json")
            if not os.path.exists(mapping_path):
                self.logger.error(f"Question mapping file not found: {mapping_path}")
                raise FileNotFoundError(f"Question mapping file not found: {mapping_path}")
            
            with open(mapping_path, "r", encoding="utf-8") as f:
                question_data = json.load(f)
            
            # Create mapping from ID to prompt text
            question_map = {
                prompt["id"]: prompt["prompt"]
                for prompt in question_data.get("text", {}).get("prompts", [])
            }
            
            # Get recommendations
            self.logger.info("Fetching recommendations for profile JSON...")
            recommendations = self.api_client.get_recommendations(
                active_today=active_today,
                new_here=new_here
            )
            
            # Extract user IDs
            user_ids = []
            for feed in recommendations.get("feeds", []):
                for subject in feed.get("subjects", []):
                    user_ids.append(subject["subjectId"])
            
            if not user_ids:
                self.logger.warning("No user IDs found in recommendations")
                return
            
            # Get profiles
            self.logger.info(f"Fetching profiles for {len(user_ids)} users...")
            profiles = self.api_client.get_public_users(user_ids)
            
            # Structure the data
            output_data = {}
            for profile in profiles:
                user_id = profile["identityId"]
                profile_data = profile.get("profile", {})
                
                # Extract profile info (excluding answers and photos)
                profile_info = {
                    k: v for k, v in profile_data.items()
                    if k not in ["answers", "photos"]
                }
                
                # Extract prompts with question text
                prompts = [
                    {
                        "question": question_map.get(answer["questionId"], "Unknown Question"),
                        "response": answer["response"]
                    }
                    for answer in profile_data.get("answers", [])
                ]
                
                # Extract image URLs
                images = [
                    photo["url"]
                    for photo in profile_data.get("photos", [])
                ]
                
                output_data[user_id] = {
                    "profile_info": profile_info,
                    "prompts": prompts,
                    "images": images
                }
            
            # Write to JSON file
            output_path = os.path.join(os.getcwd(), output_file)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2)
            self.logger.info(f"Profile data saved to {output_path}")
            
        except HingeAPIError as e:
            self.logger.error(f"API error occurred: {str(e)}")
            raise
        except FileNotFoundError as e:
            self.logger.error(str(e))
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error occurred: {str(e)}")
            raise
