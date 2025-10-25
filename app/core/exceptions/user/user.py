from typing import Any

from fastapi import HTTPException, status

from app.core.exceptions.base import AlreadyExistsError, NotFoundError


class UserNotFoundError(NotFoundError):
    def __init__(self, user_field: Any = None):
        super().__init__("User", user_field)


class UserAlreadyExistsError(AlreadyExistsError):
    def __init__(self, user_field: Any = None):
        super().__init__("User", user_field)


class AuthenticationFailedError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed"
        )
