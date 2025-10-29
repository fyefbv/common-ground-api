from typing import Any

from fastapi import HTTPException, status

from app.core.exceptions.base import AlreadyExistsError, NotFoundError


class ProfileNotFoundError(NotFoundError):
    def __init__(self, profile_field: Any = None):
        super().__init__("Profile", profile_field)


class ProfileAlreadyExistsError(AlreadyExistsError):
    def __init__(self, profile_field: Any = None):
        super().__init__("Profile", profile_field)


class ProfilePermissionError(HTTPException):
    def __init__(self, profile_field: Any = None):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Permission denied for profile {profile_field}"
                if profile_field
                else f"Permission denied for profile"
            ),
        )
        self.profile_field = profile_field
