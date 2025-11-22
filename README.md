# HingeSDK

Unofficial Python SDK for the Hinge API. Programmatically interact with Hinge to fetch recommendations, send messages, download media, and automate interactions.

## Authentication & Environment Setup

To use this SDK, you need valid authentication credentials. You can store these in a `.env` file or pass them directly to the client.

### Required Variables

*   `BEARER_TOKEN`: Your JWT authentication token (e.g., `L2euNWN...`).
*   `SESSION_ID`: The current session UUID.
*   `USER_ID`: Your unique user/player ID.

### How to Get Credentials

#### Method 1: Rooted Phone / Proxy (Recommended for Existing Accounts)
If you want to use your existing Hinge account without risking flags from new device logins, you must extract these values from the app's network traffic.

**Note:** You only need to do this **once** to obtain the correct variables. After capturing them, you can use the SMS Login method for future sessions.

1.  Use a rooted Android device or a standard proxy setup (e.g., with HTTP Toolkit or Charles Proxy) since Hinge does not use certificate pinning.
2.  Inspect HTTPS requests to `prod-api.hingeaws.net` or similar Hinge endpoints.
3.  Extract the following headers/values from the request or response bodies of profile endpoints:
    *   `authorization` (Bearer token)
    *   `x-session-id`
    *   `x-device-id`
    *   `x-install-id`
    *   `User ID` (often in the response body as `subjectId` or similar)

#### Method 2: SMS Login (Experimental)
You can generate new credentials by logging in via SMS through the SDK. This performs a fresh login flow.

```python
from hingesdk.client import HingeClient

# These IDs must match the actual values associated with your account.
# You cannot use random UUIDs; they must align with the account's registered device.
client = HingeClient.login_with_sms(
    phone_number="+15551234567", 
    device_id="your_device_id_uuid", 
    install_id="your_install_id_uuid" 
)

print(f"BEARER_TOKEN={client.auth_token}")
print(f"SESSION_ID={client.session_id}")
print(f"USER_ID={client.user_id}")
```

## Installation

Clone the repository and install the package:

```bash
git clone https://github.com/reedgraff/hingesdk
cd hingesdk
pip install .
```

## Quick Start

Here is a minimal example to authenticate and fetch user recommendations.

```python
import os
from hingesdk.api import HingeAPIClient

# Initialize with credentials
client = HingeAPIClient(
    auth_token=os.getenv("BEARER_TOKEN"),
    session_id=os.getenv("SESSION_ID"),
    user_id=os.getenv("USER_ID")
)

# Fetch recommendations
recs = client.get_recommendations()
print(f"Successfully fetched recommendations request.")
```

## Usage & Examples

<details>
<summary><b>Example: Sending a Message</b></summary>

```python
from hingesdk.client import HingeAPIClient

auth_token = 'your_auth_token'
user_id = 'your_user_id'

client = HingeAPIClient(auth_token=auth_token, user_id=user_id)
response = client.send_message(
    subject_id='receiver_id',
    message='Hello, this is a test message!'
)
print(response)
```
</details>

<details>
<summary><b>Example: Fetching User Recommendations</b></summary>

```python
from hingesdk.api import HingeAPIClient

client = HingeAPIClient(auth_token=auth_token, user_id=user_id)
recommendations = client.get_recommendations()
print(recommendations)
```
</details>

<details>
<summary><b>Example: Downloading User Images</b></summary>

```python
from hingesdk.tools import HingeTools
from hingesdk.api import HingeAPIClient
from hingesdk.media import HingeMediaClient

api_client = HingeAPIClient(auth_token=auth_token, user_id=user_id)
media_client = HingeMediaClient(auth_token=auth_token)

tools = HingeTools(api_client, media_client)
tools.download_recommendation_content(output_path='path_to_save_images')
```
</details>

<details>
<summary><b>Example: Getting User Info and Liking Profiles</b></summary>

```python
import os
import json
from hingesdk.tools import HingeTools
from hingesdk.api import HingeAPIClient
from hingesdk.media import HingeMediaClient

auth_token = os.getenv("BEARER_TOKEN")
session_id = os.getenv("SESSION_ID")
user_id = os.getenv("USER_ID")

api_client = HingeAPIClient(
    auth_token=auth_token,
    session_id=session_id,
    user_id=user_id
)
media_client = HingeMediaClient(auth_token=auth_token)
tools = HingeTools(api_client, media_client)

# Example: Get user info
tools.create_profile_json(
    source=ProfileSource.STANDOUTS,
    output_file="standouts.json"
)

# Example: Like a user 
with open("standouts.json", "r") as f:
    profiles = json.load(f)

personData = profiles["35582109789..."]

# Like a user's question
questionIDToLike = "5c4a346828fd883a24..."
response = api_client.like_profile(
    subject_id=personData["interaction_data"]["subject_id"],
    rating_token=personData["interaction_data"]["rating_token"],
    prompt={
        "questionId": questionIDToLike,
        "response": "I've been in Miami for a year and still haven't gone (╥﹏╥)"
    }
)
print(response)

# Like a user's photo
# photoIDToLike = "2c6411ac-66e4-4194-..."
# response = api_client.like_profile(
#     subject_id=personData["interaction_data"]["subject_id"],
#     rating_token=personData["interaction_data"]["rating_token"],
#     photo={
#         "contentId": photoIDToLike,
#         "comment": "So how many people have commented saying they've been here before?"
#     }
# )
# print(response)
```
</details>

<details>
<summary><b>Real World Example: University Finder (Filter Matches by Education)</b></summary>

This example demonstrates how to scrape recommendations and filter profiles based on specific criteria (e.g., top universities).

```python
def find_top_50_university_students(json_file_path, age_min=18, age_max=24):
    # List to store matching profiles
    matching_profiles = []
    
    # Dictionary of patterns for the top 50 universities (case insensitive)
    top_50_patterns = {
        "Princeton University": [r"princeton", r"\bpu\b", r"princeton\s+university"],
        "Massachusetts Institute of Technology": [r"mit", r"massachusetts\s+institute\s+of\s+technology", r"mass\s+tech"],
        "Harvard University": [r"harvard", r"\bhu\b", r"harvard\s+university"],
        "Stanford University": [r"stanford", r"\bsu\b", r"stanford\s+university"],
        "Yale University": [r"yale", r"\byu\b", r"yale\s+university"],
        "California Institute of Technology": [r"caltech", r"california\s+institute\s+of\s+technology"],
        "Duke University": [r"duke", r"\bdu\b", r"duke\s+university"],
        "Johns Hopkins University": [r"johns\s+hopkins", r"\bjhu\b", r"hopkins"],
        "Northwestern University": [r"northwestern", r"\bnu\b", r"northwestern\s+university"],
        "University of Pennsylvania": [r"upenn", r"penn", r"university\s+of\s+pennsylvania"],
        "Cornell University": [r"cornell", r"\bcu\b", r"cornell\s+university"],
        "University of Chicago": [r"uchicago", r"university\s+of\s+chicago", r"u\s+chicago"],
        "Brown University": [r"brown", r"\bbu\b", r"brown\s+university"],
        "Columbia University": [r"columbia", r"\bcu\b", r"columbia\s+university"],
        "Dartmouth College": [r"dartmouth", r"\bdc\b", r"dartmouth\s+college"],
        "University of California--Los Angeles": [r"ucla", r"university\s+of\s+california\s+los\s+angeles", r"uc\s+la"],
        "University of California, Berkeley": [r"uc\s+berkeley", r"berkeley", r"university\s+of\s+california\s+berkeley"],
        "Rice University": [r"rice", r"\bru\b", r"rice\s+university"],
        "University of Notre Dame": [r"notre\s+dame", r"\bnd\b", r"university\s+of\s+notre\s+dame"],
        "Vanderbilt University": [r"vanderbilt", r"\bvu\b", r"vandy"],
        "Carnegie Mellon University": [r"carnegie\s+mellon", r"\bcmu\b", r"cmu"],
        "University of Michigan--Ann Arbor": [r"umich", r"michigan", r"university\s+of\s+michigan"],
        "Washington University in St. Louis": [r"washu", r"washington\s+university", r"wu\s+stl"],
        "Emory University": [r"emory", r"\beu\b", r"emory\s+university"],
        "Georgetown University": [r"georgetown", r"\bgu\b", r"georgetown\s+university"],
        "University of Virginia": [r"uva", r"virginia", r"university\s+of\s+virginia"],
        "University of North Carolina--Chapel Hill": [r"unc", r"chapel\s+hill", r"university\s+of\s+north\s+carolina"],
        "University of Southern California": [r"usc", r"southern\s+california", r"university\s+of\s+southern\s+california"],
        "University of California, San Diego": [r"ucsd", r"uc\s+san\s+diego", r"university\s+of\s+california\s+san\s+diego"],
        "New York University": [r"nyu", r"new\s+york\s+university"],
        "University of Florida": [r"uf", r"florida", r"university\s+of\s+florida"],
        "The University of Texas--Austin": [r"ut\s+austin", r"utexas", r"university\s+of\s+texas"],
        "Georgia Institute of Technology": [r"gatech", r"georgia\s+tech", r"georgia\s+institute\s+of\s+technology"],
        "University of California, Davis": [r"uc\s+davis", r"ucd", r"university\s+of\s+california\s+davis"],
        "University of California--Irvine": [r"uci", r"uc\s+irvine", r"university\s+of\s+california\s+irvine"],
        "University of Illinois Urbana-Champaign": [r"uiuc", r"illinois", r"university\s+of\s+illinois"],
        "Boston College": [r"bc", r"boston\s+college"],
        "Tufts University": [r"tufts", r"\btu\b", r"tufts\s+university"],
        "University of California, Santa Barbara": [r"ucsb", r"uc\s+santa\s+barbara", r"university\s+of\s+california\s+santa\s+barbara"],
        "University of Wisconsin--Madison": [r"uw\s+madison", r"wisconsin", r"university\s+of\s+wisconsin"],
        "Boston University": [r"bu", r"boston\s+university"],
        "The Ohio State University": [r"ohio\s+state", r"osu", r"the\s+ohio\s+state\s+university"],
        "Rutgers University--New Brunswick": [r"rutgers", r"ru", r"rutgers\s+university"],
        "University of Maryland, College Park": [r"umd", r"maryland", r"university\s+of\s+maryland"],
        "University of Rochester": [r"rochester", r"\bur\b", r"university\s+of\s+rochester"],
        "Lehigh University": [r"lehigh", r"\blu\b", r"lehigh\s+university"],
        "Purdue University--Main Campus": [r"purdue", r"\bpu\b", r"purdue\s+university"],
        "University of Georgia": [r"uga", r"georgia", r"university\s+of\s+georgia"],
        "University of Washington": [r"uw", r"washington", r"university\s+of\s+washington"],
        "Wake Forest University": [r"wake\s+forest", r"\bwfu\b", r"wake"],
        "Case Western Reserve University": [r"case\s+western", r"\bcwru\b", r"case"],
        "Texas A&M University": [r"texas\s+a&m", r"tamu", r"a&m"],
        "Virginia Tech": [r"virginia\s+tech", r"vt", r"vtech"],
        "Florida State University": [r"fsu", r"florida\s+state", r"florida\s+state\s+university"],

        "University of Miami": [r'umiami', r'\bum\b', r'university\s+of\s+miami']
    }
    
    try:
        # Read the JSON file
        with open(json_file_path, 'r') as file:
            data = json.load(file)
            
        # Iterate through each user profile
        for user_id, profile in data.items():
            profile_info = profile.get('profile_info', {})
            
            # Check age range (default to configurable min/max)
            age = profile_info.get('age', 0)
            if not (age_min <= age <= age_max):
                continue
                
            # Get education list (default to empty list if not present)
            educations = profile_info.get('educations', [])
            
            # Check each education string for top 50 university references
            found_match = False
            matched_university = None
            for edu in educations:
                if not isinstance(edu, str):
                    continue
                    
                # Convert to lowercase for case-insensitive matching
                edu_lower = edu.lower()
                
                # Check each university's patterns
                for university, patterns in top_50_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, edu_lower):
                            found_match = True
                            matched_university = university
                            break
                    if found_match:
                        break
                if found_match:
                    break
            
            # If we found a match, add the profile to our results
            if found_match:
                # Get images list (default to empty list if not present)
                images = profile.get('images', [])
                image_urls = [img.get('url', '') for img in images if img.get('url')]
                
                matching_profiles.append({
                    'user_id': user_id,
                    'age': age,
                    'firstName': profile_info.get('firstName', ''),
                    'educations': educations,
                    'matched_university': matched_university,
                    'location': profile_info.get('location', {}).get('name', ''),
                    'image_urls': image_urls
                })
                
        return matching_profiles
    
    except FileNotFoundError:
        print(f"Error: File {json_file_path} not found.")
        return []
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {json_file_path}.")
        return []
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return []



def main():
    # Initialize clients with your auth token
    auth_token = os.getenv("BEARER_TOKEN")
    session_id = os.getenv("SESSION_ID")
    user_id = os.getenv("USER_ID")
    
    api_client = HingeAPIClient(
        auth_token=auth_token,
        session_id=session_id,
        user_id=user_id
    )
    media_client = HingeMediaClient(auth_token=auth_token)
    tools = HingeTools(api_client, media_client)

    # Example: Mass Scraping
    # tools.scrape_recommendations_multiple(
    #     iterations=40, # 40 seems like the max before needing to skip people...
    #     min_sleep = 20,
    #     max_sleep = 60,
    # )
    json_file_path = 'all_recommendations.json'
    csv_file_path = 'university_matches.csv'
    results = find_top_50_university_students(json_file_path)

    print(f"Found {len(results)} matching profiles.")

    # Define CSV headers with separate columns for each image
    headers = ['timestamp', 'user_id', 'name', 'age', 'location', 'education', 
            'image1', 'image2', 'image3', 'image4', 'image5', 'image6']

    # Open CSV file in append mode
    with open(csv_file_path, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        
        # Write headers if file is empty
        if csvfile.tell() == 0:
            writer.writeheader()
        
        # Write each profile as a row
        for profile in results:
            # Create a dictionary for the row
            row_data = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': profile['user_id'],
                'name': profile['firstName'],
                'age': profile['age'],
                'location': profile['location'],
                'education': ', '.join(profile['educations'])
            }
            
            # Add image URLs to separate columns
            for i in range(6):
                image_key = f'image{i+1}'
                if profile['image_urls'] and i < len(profile['image_urls']):
                    row_data[image_key] = profile['image_urls'][i]
                else:
                    row_data[image_key] = ''
            
            writer.writerow(row_data)

    print(f"Results have been appended to {csv_file_path}")
```
</details>

## Project Structure

The SDK is organized into logical modules to separate concerns.

```
hingesdk/
├── __init__.py
├── client.py       # Base HingeClient: Handles HTTP requests, headers, and Auth
├── api.py          # HingeAPIClient: Core API methods (like, message, get_recs)
├── media.py        # HingeMediaClient: Helpers for downloading/processing images
├── tools.py        # HingeTools: High-level workflows (batch scraping, exports)
├── models.py       # Pydantic models and data structures (if applicable)
├── exceptions.py   # Custom exception classes (HingeAPIError, HingeAuthError)
└── assets/         # Static resources (e.g., prompt definitions)
```

## License

This project is licensed under the MIT License.
