import os
import json
import time
import random
from typing import Dict, List, Optional
from .api import HingeAPIClient
from .media import HingeMediaClient
from .exceptions import HingeAPIError
from .models import ProfileSource
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
        if not self.logger.handlers:
            self.logger.setLevel(logging.INFO)
            handler = logging.StreamHandler()
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

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
        source: ProfileSource = ProfileSource.RECOMMENDATIONS,
        active_today: bool = False,
        new_here: bool = False,
        output_file: str = "hinge_profiles.json") -> None:
        """
        Create a JSON file with user profiles from either recommendations or standouts using question mappings.
        Includes rating tokens and interaction data for liking/commenting/messaging.
        
        Args:
            source: Data source (ProfileSource.RECOMMENDATIONS or ProfileSource.STANDOUTS, 
                default: ProfileSource.RECOMMENDATIONS)
            active_today: Filter for active today users (only for recommendations)
            new_here: Filter for new users (only for recommendations)
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
            
            # Get data based on source and store rating tokens
            user_ids = []
            rating_tokens = {}  # Dictionary to store rating tokens by user_id
            
            if source == ProfileSource.STANDOUTS:
                self.logger.info("Fetching standouts for profile JSON...")
                standouts = self.api_client.get_standouts()
                # Extract user IDs and rating tokens from standouts
                for standout in standouts.get("free", []) + standouts.get("paid", []):
                    user_id = standout["subjectId"]
                    user_ids.append(user_id)
                    rating_tokens[user_id] = standout["ratingToken"]
            else:  # ProfileSource.RECOMMENDATIONS
                self.logger.info("Fetching recommendations for profile JSON...")
                recommendations = self.api_client.get_recommendations(
                    active_today=active_today,
                    new_here=new_here
                )
                # Extract user IDs and rating tokens from recommendations
                for feed in recommendations.get("feeds", []):
                    for subject in feed.get("subjects", []):
                        user_id = subject["subjectId"]
                        user_ids.append(user_id)
                        rating_tokens[user_id] = subject["ratingToken"]
            
            if not user_ids:
                self.logger.warning(f"No user IDs found in {source.value}")
                return
            
            # Get profiles
            self.logger.info(f"Fetching profiles for {len(user_ids)} users from {source.value}...")
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

                # Extract prompts with question text and handle both text and voice responses
                prompts = []
                for answer in profile_data.get("answers", []):
                    prompt_data = {
                        "question": question_map.get(answer["questionId"], "Unknown Question"),
                        "question_id": answer["questionId"],
                        "type": answer.get("type", "text")  # Default to "text" if type not specified
                    }
                    
                    if prompt_data["type"] == "voice":
                        # Handle voice responses
                        transcription = answer.get("transcription", {})
                        prompt_data["response"] = transcription.get("transcript", "")
                        prompt_data["voice_url"] = answer.get("url")
                        prompt_data["waveform"] = answer.get("waveform")
                    else:
                        # Handle text responses
                        prompt_data["response"] = answer.get("response", "")

                    prompts.append(prompt_data)
                
                # Extract image details with additional metadata
                images = [
                    {
                        "url": photo["url"],
                        "cdn_id": photo.get("cdnId"),
                        "content_id": photo.get("contentId")
                    }
                    for photo in profile_data.get("photos", [])
                ]
                
                # Compile all interaction-relevant data
                output_data[user_id] = {
                    "profile_info": profile_info,
                    "prompts": prompts,
                    "images": images,
                    "interaction_data": {
                        "subject_id": user_id,
                        "rating_token": rating_tokens.get(user_id),
                        "source": source.value
                    }
                }
            
            # Write to JSON file
            output_path = os.path.join(os.getcwd(), output_file)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2)
            self.logger.info(f"Profile data from {source.value} saved to {output_path}")
            
        except HingeAPIError as e:
            self.logger.error(f"API error occurred: {str(e)}")
            raise
        except FileNotFoundError as e:
            self.logger.error(str(e))
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error occurred: {str(e)}")
            raise

    def scrape_recommendations_multiple(self,
        iterations: int = 40,
        output_file: str = "all_recommendations.json",
        min_sleep: float = 5.0,
        max_sleep: float = 15.0,
        active_today: bool = False,
        new_here: bool = False) -> None:
        """
        Scrape recommendations multiple times, appending unique profiles to a JSON file.
        Logs duplicate vs unique counts and includes randomized sleep intervals.
        
        Args:
            iterations: Number of times to scrape recommendations (default: 40, as I've found this to be the limit before you don't get unique options anymore)
            output_file: Path to save/append the JSON file
            min_sleep: Minimum sleep time in seconds between scrapes
            max_sleep: Maximum sleep time in seconds between scrapes
            active_today: Filter for active today users
            new_here: Filter for new users
        """
        try:
            # Load existing data if file exists
            output_path = os.path.join(os.getcwd(), output_file)
            if os.path.exists(output_path):
                with open(output_path, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
            else:
                existing_data = {}

            # Load question mappings
            mapping_path = os.path.join(os.path.dirname(__file__), "assets/prompts.json")
            if not os.path.exists(mapping_path):
                self.logger.error(f"Question mapping file not found: {mapping_path}")
                raise FileNotFoundError(f"Question mapping file not found: {mapping_path}")
            with open(mapping_path, "r", encoding="utf-8") as f:
                question_data = json.load(f)
            question_map = {prompt["id"]: prompt["prompt"] for prompt in question_data.get("text", {}).get("prompts", [])}

            # Scrape iterations
            for i in range(iterations):
                self.logger.info(f"Starting scrape iteration {i + 1}/{iterations}...")
                
                # Fetch recommendations
                recommendations = self.api_client.get_recommendations(
                    active_today=active_today,
                    new_here=new_here
                )
                user_ids = []
                rating_tokens = {}
                for feed in recommendations.get("feeds", []):
                    for subject in feed.get("subjects", []):
                        user_id = subject["subjectId"]
                        user_ids.append(user_id)
                        rating_tokens[user_id] = subject["ratingToken"]

                if not user_ids:
                    self.logger.warning("No user IDs found in this iteration")
                    continue

                # Fetch profiles
                self.logger.info(f"Fetching profiles for {len(user_ids)} users...")
                profiles = self.api_client.get_public_users(user_ids)

                # Process profiles and track unique vs duplicates
                new_profiles = 0
                duplicate_profiles = 0
                for profile in profiles:
                    user_id = profile["identityId"]
                    if user_id in existing_data:
                        duplicate_profiles += 1
                        continue  # Skip duplicates
                    
                    new_profiles += 1
                    profile_data = profile.get("profile", {})
                    profile_info = {k: v for k, v in profile_data.items() if k not in ["answers", "photos"]}
                    prompts = []
                    for answer in profile_data.get("answers", []):
                        prompt_data = {"question": question_map.get(answer["questionId"], "Unknown Question"), "question_id": answer["questionId"], "type": answer.get("type", "text")}
                        if prompt_data["type"] == "voice":
                            transcription = answer.get("transcription", {})
                            prompt_data["response"] = transcription.get("transcript", "")
                            prompt_data["voice_url"] = answer.get("url")
                            prompt_data["waveform"] = answer.get("waveform")
                        else:
                            prompt_data["response"] = answer.get("response", "")
                        prompts.append(prompt_data)
                    images = [{"url": photo["url"], "cdn_id": photo.get("cdnId"), "content_id": photo.get("contentId")} for photo in profile_data.get("photos", [])]
                    existing_data[user_id] = {
                        "profile_info": profile_info,
                        "prompts": prompts,
                        "images": images,
                        "interaction_data": {"subject_id": user_id, "rating_token": rating_tokens.get(user_id), "source": "recommendations"}
                    }

                # Log results
                self.logger.info(f"Iteration {i + 1}: Added {new_profiles} unique profiles, skipped {duplicate_profiles} duplicates. Total profiles: {len(existing_data)}")

                # Write updated data to file
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(existing_data, f, indent=2)

                # Sleep if not the last iteration
                if i < iterations - 1:
                    sleep_time = random.uniform(min_sleep, max_sleep)
                    self.logger.info(f"Sleeping for {sleep_time:.2f} seconds before next scrape...")
                    time.sleep(sleep_time)

            self.logger.info(f"Completed {iterations} scrapes. Final data saved to {output_path} with {len(existing_data)} unique profiles.")

        except HingeAPIError as e:
            self.logger.error(f"API error occurred: {str(e)}")
            raise
        except FileNotFoundError as e:
            self.logger.error(str(e))
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error occurred: {str(e)}")
            raise