from fastapi import HTTPException, status

from app.core.exceptions.base import AlreadyExistsError, NotFoundError


class ChatRouletteError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class AlreadyInSearchError(AlreadyExistsError):
    def __init__(self):
        super().__init__("Search", None)


class AlreadyInSessionError(AlreadyExistsError):
    def __init__(self):
        super().__init__("Active session", None)


class NoActiveSearchError(NotFoundError):
    def __init__(self):
        super().__init__("Active search", None)


class NoActiveSessionError(NotFoundError):
    def __init__(self):
        super().__init__("Active session", None)


class SessionNotFoundError(NotFoundError):
    def __init__(self):
        super().__init__("Session", None)


class PartnerNotFoundError(NotFoundError):
    def __init__(self):
        super().__init__("Partner", None)


class SessionExpiredError(ChatRouletteError):
    def __init__(self):
        super().__init__("Session has expired")


class SessionAlreadyEndedError(ChatRouletteError):
    def __init__(self):
        super().__init__("Session already ended")


class CannotRateYourselfError(ChatRouletteError):
    def __init__(self):
        super().__init__("Cannot rate yourself")


class AlreadyRatedError(ChatRouletteError):
    def __init__(self):
        super().__init__("Already rated this partner")


class CannotRateNonCompletedSessionError(ChatRouletteError):
    def __init__(self, current_status: str):
        super().__init__(
            f"Cannot rate session with status {current_status}. Only COMPLETED sessions can be rated."
        )
        self.current_status = current_status


class ExtensionNotApprovedError(ChatRouletteError):
    def __init__(self):
        super().__init__("Extension not approved by partner")


class NoMatchingFoundError(ChatRouletteError):
    def __init__(self):
        super().__init__("No matching partner found. Please try again.")
