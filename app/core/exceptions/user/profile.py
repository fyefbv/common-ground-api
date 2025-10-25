from typing import Any

from app.core.exceptions.base import AlreadyExistsError, NotFoundError


class ProfileNotFoundError(NotFoundError):
    def __init__(self, profile_field: Any = None):
        super().__init__("Profile", profile_field)


class ProfileAlreadyExistsError(AlreadyExistsError):
    def __init__(self, profile_field: Any = None):
        super().__init__("Profile", profile_field)
