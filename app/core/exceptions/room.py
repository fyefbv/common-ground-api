from fastapi import HTTPException, status

from app.core.exceptions.base import AlreadyExistsError, NotFoundError


class RoomNotFoundError(NotFoundError):
    def __init__(self, room_field: str | None = None):
        super().__init__("Room", room_field)


class RoomAlreadyExistsError(AlreadyExistsError):
    def __init__(self, room_field: str | None = None):
        super().__init__("Room", room_field)


class RoomPermissionError(HTTPException):
    def __init__(self, detail: str = "Permission denied for room"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class RoomFullError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Room is full",
        )


class RoomPrivateError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Room is private",
        )


class NotRoomMemberError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this room",
        )


class RoomParticipantNotFoundError(NotFoundError):
    def __init__(self, participant_field: str | None = None):
        super().__init__("Room participant", participant_field)


class ParticipantBannedError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Participant is banned from this room",
        )


class ParticipantMutedError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Participant is muted",
        )


class RoomMessageNotFoundError(NotFoundError):
    def __init__(self, message_field: str | None = None):
        super().__init__("Room message", message_field)


class InvalidRoleError(HTTPException):
    def __init__(self, role: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {role}. Must be either MEMBER or MODERATOR",
        )


class ParticipantAlreadyHasRoleError(HTTPException):
    def __init__(self, role: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Participant already has role {role}",
        )
