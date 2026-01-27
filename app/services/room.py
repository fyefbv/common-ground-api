from datetime import datetime
from uuid import UUID

from app.core.exceptions.room import (
    InvalidRoleError,
    NotRoomMemberError,
    ParticipantAlreadyHasRoleError,
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
from app.services.websocket.room import WebSocketRoomService


class RoomService:
    def __init__(self, uow: UnitOfWork, wrs: WebSocketRoomService):
        self.uow = uow
        self.wrs = wrs

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

            room_response = RoomResponse(
                id=updated_room.id,
                name=updated_room.name,
                description=updated_room.description,
                primary_interest_id=updated_room.primary_interest_id,
                creator_id=updated_room.creator_id,
                tags=updated_room.tags,
                max_participants=updated_room.max_participants,
                is_private=updated_room.is_private,
                participants_count=participants_count,
                messages_count=messages_count,
                created_at=updated_room.created_at,
                updated_at=updated_room.updated_at,
                is_joined=True,
            )

            try:
                await self.wrs.broadcast_room_update(
                    room_id, room_response.model_dump(), profile_id
                )
            except Exception as e:
                app_logger.error(
                    f"Ошибка при отправке WebSocket уведомления об обновлении комнаты: {e}"
                )

            return room_response

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

            try:
                await self.wrs.broadcast_room_deleted(room_id, profile_id)
            except Exception as e:
                app_logger.error(
                    f"Ошибка при отправке WebSocket уведомления об удалении комнаты: {e}"
                )

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

            try:
                await self.wrs.broadcast_participant_joined(room_id, profile_id)
            except Exception as e:
                app_logger.error(
                    f"Ошибка при отправке WebSocket уведомления о присоединении участника: {e}"
                )

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

            try:
                await self.wrs.broadcast_participant_left(room_id, profile_id)
            except Exception as e:
                app_logger.error(
                    f"Ошибка при отправке WebSocket уведомления о выходе участника: {e}"
                )

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

            if participant.is_banned:
                raise ParticipantBannedError()

            participants = await uow.room_participant.get_room_participants(
                room_id=room_id, include_banned=include_banned
            )

            participants_response = []
            for p in participants:
                participant_dict = p.__dict__.copy()

                participant_dict["is_online"] = self.wrs.is_profile_online(
                    room_id, p.profile_id
                )

                participant_response = RoomParticipantResponse.model_validate(
                    participant_dict
                )
                participants_response.append(participant_response)

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

            if requester.is_banned:
                raise ParticipantBannedError()

            room = await uow.room.get_by_id(room_id)
            if not room:
                raise RoomNotFoundError(room_id)

            is_creator = room.creator_id == profile_id

            if not is_creator and requester.role != RoomParticipantRole.MODERATOR:
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

            if target.role == RoomParticipantRole.MODERATOR and not is_creator:
                raise RoomPermissionError("Moderators cannot kick other moderators")

            await uow.room_participant.remove_participant(
                room_id, kick_request.profile_id
            )
            await uow.commit()

            app_logger.info(
                f"Участник {kick_request.profile_id} исключен из комнаты {room_id}"
            )

            try:
                await self.wrs.broadcast_participant_kicked(
                    room_id, kick_request.profile_id, profile_id
                )
            except Exception as e:
                app_logger.error(
                    f"Ошибка при отправке WebSocket уведомления об исключении участника: {e}"
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

            try:
                message_response = RoomMessageResponse.model_validate(message)

                await self.wrs.broadcast_new_message(
                    room_id, message_response.model_dump(), profile_id
                )
            except Exception as e:
                app_logger.error(
                    f"Ошибка при отправке WebSocket уведомления о новом сообщении: {e}"
                )

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

            if participant.is_banned:
                raise ParticipantBannedError()

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

            participant = await uow.room_participant.get_participant(
                message.room_id, profile_id
            )
            if not participant:
                raise NotRoomMemberError()

            if participant.is_banned:
                raise ParticipantBannedError()

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

            if participant.is_banned:
                raise ParticipantBannedError()

            if message.sender_id != profile_id and participant.role not in [
                RoomParticipantRole.CREATOR,
                RoomParticipantRole.MODERATOR,
            ]:
                raise RoomPermissionError("Cannot delete messages from other users")

            await uow.room_message.soft_delete_message(message_id)

            await uow.commit()

            app_logger.info(f"Сообщение {message_id} удалено")

    async def mute_participant(
        self, room_id: UUID, target_profile_id: UUID, profile_id: UUID
    ) -> None:
        app_logger.info(f"Мут участника {target_profile_id} в комнате {room_id}")

        async with self.uow as uow:
            room = await uow.room.get_by_id(room_id)
            if not room:
                raise RoomNotFoundError(room_id)

            requester = await uow.room_participant.get_participant(room_id, profile_id)
            if not requester:
                raise NotRoomMemberError()

            if requester.is_banned:
                raise ParticipantBannedError()

            is_creator = room.creator_id == profile_id
            if not is_creator and requester.role != RoomParticipantRole.MODERATOR:
                raise RoomPermissionError(
                    "Only creators and moderators can mute participants"
                )

            if target_profile_id == profile_id:
                raise RoomPermissionError("Cannot mute yourself")

            target = await uow.room_participant.get_participant(
                room_id, target_profile_id
            )
            if not target:
                raise RoomParticipantNotFoundError(target_profile_id)

            if room.creator_id == target_profile_id:
                raise RoomPermissionError("Cannot mute room creator")

            if target.role == RoomParticipantRole.MODERATOR and not is_creator:
                raise RoomPermissionError("Moderators cannot mute other moderators")

            await uow.room_participant.mute_participant(room_id, target_profile_id)
            await uow.commit()

            app_logger.info(f"Участник {target_profile_id} замучен в комнате {room_id}")

            try:
                await self.wrs.broadcast_participant_muted(
                    room_id, target_profile_id, profile_id
                )
            except Exception as e:
                app_logger.error(
                    f"Ошибка при отправке WebSocket уведомления о мьюте участника: {e}"
                )

    async def unmute_participant(
        self, room_id: UUID, target_profile_id: UUID, profile_id: UUID
    ) -> None:
        app_logger.info(
            f"Снятие мута с участника {target_profile_id} в комнате {room_id}"
        )

        async with self.uow as uow:
            room = await uow.room.get_by_id(room_id)
            if not room:
                raise RoomNotFoundError(room_id)

            requester = await uow.room_participant.get_participant(room_id, profile_id)
            if not requester:
                raise NotRoomMemberError()

            if requester.is_banned:
                raise ParticipantBannedError()

            is_creator = room.creator_id == profile_id
            if not is_creator and requester.role != RoomParticipantRole.MODERATOR:
                raise RoomPermissionError(
                    "Only creators and moderators can unmute participants"
                )

            target = await uow.room_participant.get_participant(
                room_id, target_profile_id
            )
            if not target:
                raise RoomParticipantNotFoundError(target_profile_id)

            await uow.room_participant.unmute_participant(room_id, target_profile_id)
            await uow.commit()

            app_logger.info(
                f"С участника {target_profile_id} снят мут в комнате {room_id}"
            )

            try:
                await self.wrs.broadcast_participant_unmuted(
                    room_id, target_profile_id, profile_id
                )
            except Exception as e:
                app_logger.error(
                    f"Ошибка при отправке WebSocket уведомления о размьюте участника: {e}"
                )

    async def ban_participant(
        self, room_id: UUID, target_profile_id: UUID, profile_id: UUID
    ) -> None:
        app_logger.info(f"Бан участника {target_profile_id} в комнате {room_id}")

        async with self.uow as uow:
            room = await uow.room.get_by_id(room_id)
            if not room:
                raise RoomNotFoundError(room_id)

            requester = await uow.room_participant.get_participant(room_id, profile_id)
            if not requester:
                raise NotRoomMemberError()

            if requester.is_banned:
                raise ParticipantBannedError()

            is_creator = room.creator_id == profile_id
            if not is_creator and requester.role != RoomParticipantRole.MODERATOR:
                raise RoomPermissionError(
                    "Only creators and moderators can ban participants"
                )

            if target_profile_id == profile_id:
                raise RoomPermissionError("Cannot ban yourself")

            target = await uow.room_participant.get_participant(
                room_id, target_profile_id
            )
            if not target:
                raise RoomParticipantNotFoundError(target_profile_id)

            if room.creator_id == target_profile_id:
                raise RoomPermissionError("Cannot ban room creator")

            if target.role == RoomParticipantRole.MODERATOR and not is_creator:
                raise RoomPermissionError("Moderators cannot ban other moderators")

            await uow.room_participant.ban_participant(room_id, target_profile_id)
            await uow.commit()

            app_logger.info(f"Участник {target_profile_id} забанен в комнате {room_id}")

            try:
                await self.wrs.broadcast_participant_banned(
                    room_id, target_profile_id, profile_id
                )
            except Exception as e:
                app_logger.error(
                    f"Ошибка при отправке WebSocket уведомления о бане участника: {e}"
                )

    async def unban_participant(
        self, room_id: UUID, target_profile_id: UUID, profile_id: UUID
    ) -> None:
        app_logger.info(f"Разбан участника {target_profile_id} в комнате {room_id}")

        async with self.uow as uow:
            room = await uow.room.get_by_id(room_id)
            if not room:
                raise RoomNotFoundError(room_id)

            requester = await uow.room_participant.get_participant(room_id, profile_id)
            if not requester:
                raise NotRoomMemberError()

            if requester.is_banned:
                raise ParticipantBannedError()

            is_creator = room.creator_id == profile_id
            if not is_creator and requester.role != RoomParticipantRole.MODERATOR:
                raise RoomPermissionError(
                    "Only creators and moderators can unban participants"
                )

            target = await uow.room_participant.get_participant(
                room_id, target_profile_id
            )
            if not target:
                raise RoomParticipantNotFoundError(target_profile_id)

            await uow.room_participant.unban_participant(room_id, target_profile_id)
            await uow.commit()

            app_logger.info(
                f"Участник {target_profile_id} разбанен в комнате {room_id}"
            )

            try:
                await self.wrs.broadcast_participant_unbanned(
                    room_id, target_profile_id, profile_id
                )
            except Exception as e:
                app_logger.error(
                    f"Ошибка при отправке WebSocket уведомления о разбане участника: {e}"
                )

    async def get_banned_participants(
        self, room_id: UUID, profile_id: UUID
    ) -> list[RoomParticipantResponse]:
        app_logger.info(f"Получение забаненных участников комнаты: {room_id}")

        async with self.uow as uow:
            participant = await uow.room_participant.get_participant(
                room_id, profile_id
            )
            if not participant:
                raise NotRoomMemberError()

            if participant.is_banned:
                raise ParticipantBannedError()

            room = await uow.room.get_by_id(room_id)
            if not room:
                raise RoomNotFoundError(room_id)

            if (
                room.creator_id != profile_id
                and participant.role != RoomParticipantRole.MODERATOR
            ):
                raise RoomPermissionError(
                    "Only creators and moderators can view banned participants"
                )

            participants = await uow.room_participant.get_room_participants(
                room_id=room_id, include_banned=True
            )

            banned_participants = [p for p in participants if p.is_banned]

            participants_response = []
            for p in banned_participants:
                participant_dict = p.__dict__.copy()

                participant_dict["is_online"] = self.wrs.is_profile_online(
                    room_id, p.profile_id
                )

                participant_response = RoomParticipantResponse.model_validate(
                    participant_dict
                )
                participants_response.append(participant_response)

            app_logger.info(
                f"Найдено {len(participants_response)} забаненных участников"
            )
            return participants_response

    async def change_participant_role(
        self,
        room_id: UUID,
        target_profile_id: UUID,
        new_role: RoomParticipantRole,
        profile_id: UUID,
    ) -> RoomParticipantResponse:
        app_logger.info(
            f"Изменение роли участника {target_profile_id} в комнате {room_id}"
        )

        async with self.uow as uow:
            room = await uow.room.get_by_id(room_id)
            if not room:
                raise RoomNotFoundError(room_id)

            if room.creator_id != profile_id:
                raise RoomPermissionError(
                    "Only room creator can change participant roles"
                )

            requester = await uow.room_participant.get_participant(room_id, profile_id)
            if not requester:
                raise NotRoomMemberError()

            target_participant = await uow.room_participant.get_participant(
                room_id, target_profile_id
            )
            if not target_participant:
                raise RoomParticipantNotFoundError(target_profile_id)

            if target_participant.role == RoomParticipantRole.CREATOR:
                raise RoomPermissionError("Cannot change role of room creator")

            if new_role not in [
                RoomParticipantRole.MEMBER,
                RoomParticipantRole.MODERATOR,
            ]:
                raise InvalidRoleError(new_role.value)

            if target_participant.role == new_role:
                raise ParticipantAlreadyHasRoleError(new_role.value)

            old_role = target_participant.role

            await uow.room_participant.update_role(
                room_id=room_id,
                profile_id=target_profile_id,
                role=new_role,
            )

            await uow.commit()

            updated_participant = await uow.room_participant.get_participant(
                room_id, target_profile_id
            )

            is_online = self.wrs.is_profile_online(room_id, target_profile_id)

            app_logger.info(
                f"Роль участника {target_profile_id} изменена с {old_role} на {new_role} в комнате {room_id}"
            )

            participant_dict = {
                **updated_participant.__dict__,
                "is_online": is_online,
            }

            participant_response = RoomParticipantResponse.model_validate(
                participant_dict
            )

            try:
                await self.wrs.broadcast_role_changed(
                    room_id=room_id,
                    target_profile_id=target_profile_id,
                    old_role=old_role,
                    new_role=new_role,
                    changer_profile_id=profile_id,
                )
            except Exception as e:
                app_logger.error(
                    f"Ошибка при отправке WebSocket уведомления о смене роли участника: {e}"
                )

            return participant_response
