# HingeSDK

HingeAPI is a Python library designed to interact with the Hinge app's API, allowing you to perform various operations such as sending messages, fetching user recommendations, and downloading media content.

## Getting Started

### Prerequisites

- Python 3.x
- `requests` library

You can install the required packages using pip:

```bash
pip install requests
```

### Installation

Clone this repository to your local machine:

```bash
git clone https://github.com/ReedGraff/HingeSDK.git
```

Navigate to the project directory:

```bash
cd HingeAPI
```

### Usage

To use this library, you'll need to initialize the `HingeClient` with your authentication details. The client classes provided in this package include `HingeClient`, `HingeMediaClient`, and `HingeAPIClient`.

#### Example: Sending a Message

```python
from hingeapi.client import HingeAPIClient

auth_token = 'your_auth_token'
user_id = 'your_user_id'

client = HingeAPIClient(auth_token=auth_token, user_id=user_id)
response = client.send_message(
    subject_id='receiver_id',
    message='Hello, this is a test message!'
)
print(response)
```

#### Example: Fetching User Recommendations

```python
from hingeapi.api import HingeAPIClient

client = HingeAPIClient(auth_token=auth_token, user_id=user_id)
recommendations = client.get_recommendations()
print(recommendations)
```

#### Example: Downloading User Images

```python
from hingeapi.tools import HingeTools
from hingeapi.api import HingeAPIClient
from hingeapi.media import HingeMediaClient

api_client = HingeAPIClient(auth_token=auth_token, user_id=user_id)
media_client = HingeMediaClient(auth_token=auth_token)

tools = HingeTools(api_client, media_client)
tools.download_recommendation_content(output_path='path_to_save_images')
```

#### Example: Getting User Info and Liking Profiles

```python
import os
import json
from hingeapi.tools import HingeTools
from hingeapi.api import HingeAPIClient
from hingeapi.media import HingeMediaClient

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

## Available Classes and Functions

- `HingeClient`: Base client handling HTTP requests and authentication.
- `HingeAPIClient`: Interaction with the Hinge API for various operations, including sending messages and fetching recommendations.
- `HingeMediaClient`: Operations for downloading and processing media content from Hinge.
- `HingeTools`: Advanced operations using both API and media functionalities.

## Error Handling

The library provides custom exceptions to handle various error scenarios:
- `HingeAPIError`: General API errors.
- `HingeAuthError`: Authentication-related errors.

<!--

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Please read [CONTRIBUTING](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests.
-->
