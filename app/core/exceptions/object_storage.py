from fastapi import HTTPException, status


class ObjectUploadError(HTTPException):
    def __init__(self, object_name: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload object {object_name}",
        )


class ObjectDeleteError(HTTPException):
    def __init__(self, object_name: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete object {object_name}",
        )


class ObjectListGetError(HTTPException):
    def __init__(self, object_name: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get the {object_name} object list",
        )
