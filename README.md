# HingeAPI

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
git clone <repository-url>
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
