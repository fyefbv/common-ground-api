from fastapi import HTTPException, status


class UnsupportedMediaTypeError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=detail
        )


class FileTooLargeError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=detail
        )
