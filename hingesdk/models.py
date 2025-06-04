from dataclasses import dataclass
from typing import Optional, Dict, List
from enum import Enum


class ProfileSource(Enum):
    """Enum for profile data sources"""

    RECOMMENDATIONS = "recommendations"
    STANDOUTS = "standouts"


@dataclass
class UserSettings:
    is_smart_photo_opt_in: bool


@dataclass
class AuthSettings:
    apple_authed: bool
    facebook_authed: bool
    google_authed: bool
    sms_authed: bool


@dataclass
class NotificationSettings:
    email: Dict[str, bool]
    push: Dict[str, bool]


@dataclass
class LikeLimit:
    likes_left: int
    superlikes_left: int
    free_superlikes_left: int
    free_superlike_expiration: str


@dataclass
class UserTrait:
    id: str
    user_input: str


@dataclass
class AccountInfo:
    subscription: Dict
    account: Dict[str, bool]
