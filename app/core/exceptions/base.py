from typing import Any

from fastapi import HTTPException, status


class NotFoundError(HTTPException):
    def __init__(self, entity_name: str, entity_field: Any = None):
        detail = (
            f"{entity_name} {entity_field} not found"
            if entity_field
            else f"{entity_name} not found"
        )
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
        self.entity_field = entity_field


class AlreadyExistsError(HTTPException):
    def __init__(self, entity_name: str, entity_field: Any = None):
        detail = (
            f"{entity_name} {entity_field} already exists"
            if entity_field
            else f"{entity_name} already exists"
        )
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
        self.entity_field = entity_field
