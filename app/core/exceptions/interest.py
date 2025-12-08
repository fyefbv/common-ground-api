from typing import Any

from app.core.exceptions.base import NotFoundError


class InterestNotFoundError(NotFoundError):
    def __init__(self, interest_field: Any = None):
        super().__init__("Interest", interest_field)
