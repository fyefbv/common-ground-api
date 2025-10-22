from fastapi import Depends

from app.core.auth import decode_jwt, oauth2_scheme
from app.core.exceptions.user import MissingTokenError
from app.db.unit_of_work import UnitOfWork
from app.services.user import UserService


async def get_unit_of_work() -> UnitOfWork:
    return UnitOfWork()


async def get_user_service(uow: UnitOfWork = Depends(get_unit_of_work)) -> UserService:
    return UserService(uow)


async def get_current_user_email(token: str = Depends(oauth2_scheme)):
    if not token:
        raise MissingTokenError()

    payload = decode_jwt(token)
    return payload.get("sub")
