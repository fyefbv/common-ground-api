from fastapi import HTTPException, status
from typing import Any


class UserNotFoundError(HTTPException):
    def __init__(self, user_id: Any = None):
        detail = f"User {user_id} not found" if user_id else "User not found"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )
        self.user_id = user_id

class EmailAlreadyExistsError(HTTPException):
    def __init__(self, email: str):
        detail = f"User with email {email} already exists"
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )
        self.email = email