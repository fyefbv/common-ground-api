from datetime import datetime, timezone
from uuid import UUID

from app.core.exceptions.room import (
    NotRoomMemberError,
    ParticipantBannedError,
    ParticipantMutedError,
    RoomAlreadyExistsError,
    RoomFullError,
    RoomMessageNotFoundError,
    RoomNotFoundError,
    RoomParticipantNotFoundError,
    RoomPermissionError,
    RoomPrivateError,
)
from app.core.logger import app_logger
from app.db.models.room_participant import RoomParticipantRole
from app.db.unit_of_work import UnitOfWork
from app.schemas.room import RoomCreate, RoomResponse, RoomUpdate
from app.schemas.room_message import (
    RoomMessageCreate,
    RoomMessageListResponse,
    RoomMessageResponse,
    RoomMessageUpdate,
)
from app.schemas.room_participant import RoomKickRequest, RoomParticipantResponse


class RoomService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def create_room(
        self, room_create: RoomCreate, profile_id: UUID
    ) -> RoomResponse:
        app_logger.info(f"Создание комнаты: {room_create.name}")

        async with self.uow as uow:
            existing_room = await uow.room.find_by_name(room_create.name)
            if existing_room:
                raise RoomAlreadyExistsError(room_create.name)

            room_data = room_create.model_dump()
            room_data["creator_id"] = profile_id

            room = await uow.room.add_one(room_data)

            await uow.room_participant.add_participant(
                room_id=room.id, profile_id=profile_id, role=RoomParticipantRole.CREATOR
            )

            participants_count, messages_count = (
                await uow.room_participant.get_room_counts(room.id)
            )

            await uow.commit()

            app_logger.info(f"Комната создана с ID: {room.id}")

            room_dict = {
                **room.__dict__,
                "participants_count": participants_count,
                "messages_count": messages_count,
                "is_joined": True,
            }
            return RoomResponse(**room_dict)

    async def get_room(
        self, room_id: UUID, profile_id: UUID | None = None
    ) -> RoomResponse:
        app_logger.info(f"Получение комнаты: {room_id}")

        async with self.uow as uow:
            room = await uow.room.get_by_id(room_id)
            if not room:
                raise RoomNotFoundError(room_id)

            participants_count, messages_count = (
                await uow.room_participant.get_room_counts(room_id)
            )

            is_joined = False
            if profile_id:
                participant = await uow.room_participant.get_participant(
                    room_id, profile_id
                )
                is_joined = participant is not None and not participant.is_banned

            room_dict = {
                **room.__dict__,
                "participants_count": participants_count,
                "messages_count": messages_count,
                "is_joined": is_joined,
            }

            return RoomResponse(**room_dict)

    async def search_rooms(
        self,
        query: str | None = None,
        interest_id: UUID | None = None,
        tags: list[str] | None = None,
        is_private: bool | None = False,
        limit: int = 50,
        offset: int = 0,
        profile_id: UUID | None = None,
    ) -> list[RoomResponse]:
        app_logger.info(f"Поиск комнат: query={query}, interest_id={interest_id}")

        async with self.uow as uow:
            rooms = await uow.room.search_rooms(
                query=query,
                interest_id=interest_id,
                tags=tags,
                is_private=is_private,
                limit=limit,
                offset=offset,
            )

            rooms_response = []
            for room in rooms:
                participants_count, messages_count = (
                    await uow.room_participant.get_room_counts(room.id)
                )

                is_joined = False
                if profile_id:
                    participant = await uow.room_participant.get_participant(
                        room.id, profile_id
                    )
                    is_joined = participant is not None and not participant.is_banned

                room_dict = {
                    **room.__dict__,
                    "participants_count": participants_count,
                    "messages_count": messages_count,
                    "is_joined": is_joined,
                }
                rooms_response.append(RoomResponse(**room_dict))

            app_logger.info(f"Найдено {len(rooms_response)} комнат")
            return rooms_response

    async def get_popular_rooms(
        self, limit: int = 20, profile_id: UUID | None = None
    ) -> list[RoomResponse]:
        app_logger.info("Получение популярных комнат")

        async with self.uow as uow:
            rooms = await uow.room.get_popular_rooms(limit=limit)

            rooms_response = []
            for room in rooms:
                participants_count, messages_count = (
                    await uow.room_participant.get_room_counts(room.id)
                )

                is_joined = False
                if profile_id:
                    participant = await uow.room_participant.get_participant(
                        room.id, profile_id
                    )
                    is_joined = participant is not None and not participant.is_banned

                room_dict = {
                    **room.__dict__,
                    "participants_count": participants_count,
                    "messages_count": messages_count,
                    "is_joined": is_joined,
                }
                rooms_response.append(RoomResponse(**room_dict))

            return rooms_response

    async def get_user_rooms(self, profile_id: UUID) -> list[RoomResponse]:
        app_logger.info(f"Получение комнат профиля: {profile_id}")

        async with self.uow as uow:
            rooms = await uow.room.find_all(creator_id=profile_id)
            rooms.sort(key=lambda r: r.created_at, reverse=True)

            rooms_response = []
            for room in rooms:
                participants_count, messages_count = (
                    await uow.room_participant.get_room_counts(room.id)
                )

                participant = await uow.room_participant.get_participant(
                    room.id, profile_id
                )
                is_joined = participant is not None and not participant.is_banned

                room_dict = {
                    **room.__dict__,
                    "participants_count": participants_count,
                    "messages_count": messages_count,
                    "is_joined": is_joined,
                }
                rooms_response.append(RoomResponse(**room_dict))

            app_logger.info(
                f"Найдено {len(rooms_response)} комнат профиля {profile_id}"
            )
            return rooms_response

    async def update_room(
        self, room_id: UUID, room_update: RoomUpdate, profile_id: UUID
    ) -> RoomResponse:
        app_logger.info(f"Обновление комнаты: {room_id}")

        async with self.uow as uow:
            room = await uow.room.get_by_id(room_id)
            if not room:
                raise RoomNotFoundError(room_id)

            if room.creator_id != profile_id:
                raise RoomPermissionError("Only room creator can update room")

            if room_update.name and room_update.name != room.name:
                existing_room = await uow.room.find_by_name(room_update.name)
                if existing_room:
                    raise RoomAlreadyExistsError(room_update.name)

            update_data = room_update.model_dump(exclude_unset=True)
            updated_room = await uow.room.update(room_id, update_data)
            if not updated_room:
                raise RoomNotFoundError(room_id)

            participants_count, messages_count = (
                await uow.room_participant.get_room_counts(room_id)
            )

            await uow.commit()

            app_logger.info(f"Комната {room_id} обновлена")

            room_dict = {
                **updated_room.__dict__,
                "participants_count": participants_count,
                "messages_count": messages_count,
                "is_joined": True,
            }
            return RoomResponse(**room_dict)

    async def delete_room(self, room_id: UUID, profile_id: UUID) -> None:
        app_logger.info(f"Удаление комнаты: {room_id}")

        async with self.uow as uow:
            room = await uow.room.get_by_id(room_id)
            if not room:
                raise RoomNotFoundError(room_id)

            if room.creator_id != profile_id:
                raise RoomPermissionError("Only room creator can delete room")

            await uow.room.delete(room_id)
            await uow.commit()

            app_logger.info(f"Комната {room_id} удалена")

    async def join_room(self, room_id: UUID, profile_id: UUID) -> RoomResponse:
        app_logger.info(f"Присоединение к комнате: {room_id}")

        async with self.uow as uow:
            room = await uow.room.get_by_id(room_id)
            if not room:
                raise RoomNotFoundError(room_id)

            if room.is_private:
                raise RoomPrivateError()

            participant = await uow.room_participant.get_participant(
                room_id, profile_id
            )
            if participant and participant.is_banned:
                raise ParticipantBannedError()

            participants_count, _ = await uow.room_participant.get_room_counts(room_id)
            if participants_count >= room.max_participants:
                raise RoomFullError()

            if not participant:
                await uow.room_participant.add_participant(
                    room_id=room_id,
                    profile_id=profile_id,
                    role=RoomParticipantRole.MEMBER,
                )

            participants_count, messages_count = (
                await uow.room_participant.get_room_counts(room_id)
            )

            await uow.commit()

            app_logger.info(f"Профиль {profile_id} присоединился к комнате {room_id}")

            room_dict = {
                **room.__dict__,
                "participants_count": participants_count,
                "messages_count": messages_count,
                "is_joined": True,
            }
            return RoomResponse(**room_dict)

    async def leave_room(self, room_id: UUID, profile_id: UUID) -> None:
        app_logger.info(f"Выход из комнаты: {room_id}")

        async with self.uow as uow:
            participant = await uow.room_participant.get_participant(
                room_id, profile_id
            )
            if not participant:
                raise NotRoomMemberError()

            room = await uow.room.get_by_id(room_id)
            if not room:
                raise RoomNotFoundError(room_id)

            if room.creator_id == profile_id:
                raise RoomPermissionError(
                    "Room creator cannot leave room. Delete room instead."
                )

            await uow.room_participant.remove_participant(room_id, profile_id)
            await uow.commit()

            app_logger.info(f"Профиль {profile_id} вышел из комнаты {room_id}")

    async def get_room_participants(
        self, room_id: UUID, profile_id: UUID, include_banned: bool = False
    ) -> list[RoomParticipantResponse]:
        app_logger.info(f"Получение участников комнаты: {room_id}")

        async with self.uow as uow:
            participant = await uow.room_participant.get_participant(
                room_id, profile_id
            )
            if not participant:
                raise NotRoomMemberError()

            participants = await uow.room_participant.get_room_participants(
                room_id=room_id, include_banned=include_banned
            )

            participants_response = [
                RoomParticipantResponse.model_validate(p) for p in participants
            ]

            app_logger.info(f"Найдено {len(participants_response)} участников")
            return participants_response

    async def kick_participant(
        self, room_id: UUID, kick_request: RoomKickRequest, profile_id: UUID
    ) -> None:
        app_logger.info(
            f"Исключение участника {kick_request.profile_id} из комнаты {room_id}"
        )

        async with self.uow as uow:
            requester = await uow.room_participant.get_participant(room_id, profile_id)
            if not requester:
                raise NotRoomMemberError()

            room = await uow.room.get_by_id(room_id)
            if not room:
                raise RoomNotFoundError(room_id)

            is_creator = room.creator_id == profile_id

            if not is_creator and requester.role != RoomParticipantRole.MODERATOR.value:
                raise RoomPermissionError(
                    "Only creators and moderators can kick participants"
                )

            if kick_request.profile_id == profile_id:
                raise RoomPermissionError("Cannot kick yourself")

            target = await uow.room_participant.get_participant(
                room_id, kick_request.profile_id
            )
            if not target:
                raise RoomParticipantNotFoundError(kick_request.profile_id)

            if room.creator_id == kick_request.profile_id:
                raise RoomPermissionError("Cannot kick room creator")

            if target.role == RoomParticipantRole.MODERATOR.value and not is_creator:
                raise RoomPermissionError("Moderators cannot kick other moderators")

            await uow.room_participant.remove_participant(
                room_id, kick_request.profile_id
            )
            await uow.commit()

            app_logger.info(
                f"Участник {kick_request.profile_id} исключен из комнаты {room_id}"
            )

    async def send_message(
        self, room_id: UUID, message_create: RoomMessageCreate, profile_id: UUID
    ) -> RoomMessageResponse:
        app_logger.info(f"Отправка сообщения в комнату: {room_id}")

        async with self.uow as uow:
            participant = await uow.room_participant.get_participant(
                room_id, profile_id
            )
            if not participant:
                raise NotRoomMemberError()

            if participant.is_banned:
                raise ParticipantBannedError()

            if participant.is_muted:
                raise ParticipantMutedError()

            message_data = message_create.model_dump()
            message_data["room_id"] = room_id
            message_data["sender_id"] = profile_id

            message = await uow.room_message.add_one(message_data)

            await uow.commit()

            app_logger.info(f"Сообщение отправлено в комнату {room_id}")
            return RoomMessageResponse.model_validate(message)

    async def get_room_messages(
        self,
        room_id: UUID,
        profile_id: UUID,
        before: datetime | None = None,
        limit: int = 50,
    ) -> RoomMessageListResponse:
        app_logger.info(f"Получение сообщений комнаты: {room_id}")

        async with self.uow as uow:
            participant = await uow.room_participant.get_participant(
                room_id, profile_id
            )
            if not participant:
                raise NotRoomMemberError()

            messages = await uow.room_message.get_room_messages(
                room_id=room_id, before=before, limit=limit
            )

            messages_response = [
                RoomMessageResponse.model_validate(msg) for msg in messages
            ]

            app_logger.info(f"Найдено {len(messages_response)} сообщений")
            return RoomMessageListResponse(
                messages=messages_response,
                total=len(messages_response),
                has_more=len(messages_response) == limit,
            )

    async def update_message(
        self, message_id: UUID, message_update: RoomMessageUpdate, profile_id: UUID
    ) -> RoomMessageResponse:
        app_logger.info(f"Обновление сообщения: {message_id}")

        async with self.uow as uow:
            message = await uow.room_message.get_by_id(message_id)
            if not message:
                raise RoomMessageNotFoundError(message_id)

            if message.sender_id != profile_id:
                raise RoomPermissionError("Only message sender can update message")

            if message.is_deleted:
                raise RoomPermissionError("Cannot update deleted message")

            update_data = message_update.model_dump()
            updated_message = await uow.room_message.update(message_id, update_data)
            if not updated_message:
                raise RoomMessageNotFoundError(message_id)

            await uow.room_message.mark_as_edited(message_id)

            await uow.commit()

            app_logger.info(f"Сообщение {message_id} обновлено")
            return RoomMessageResponse.model_validate(updated_message)

    async def delete_message(self, message_id: UUID, profile_id: UUID) -> None:
        app_logger.info(f"Удаление сообщения: {message_id}")

        async with self.uow as uow:
            message = await uow.room_message.get_by_id(message_id)
            if not message:
                raise RoomMessageNotFoundError(message_id)

            participant = await uow.room_participant.get_participant(
                message.room_id, profile_id
            )
            if not participant:
                raise NotRoomMemberError()

            if message.sender_id != profile_id and participant.role not in [
                RoomParticipantRole.CREATOR,
                RoomParticipantRole.MODERATOR,
            ]:
                raise RoomPermissionError("Cannot delete messages from other users")

            await uow.room_message.soft_delete_message(message_id)

            await uow.commit()

            app_logger.info(f"Сообщение {message_id} удалено")
