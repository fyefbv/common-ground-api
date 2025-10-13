from fastapi import Depends

from app.db.unit_of_work import UnitOfWork
from app.services.user import UserService


async def get_unit_of_work() -> UnitOfWork:
    return UnitOfWork()


async def get_user_service(uow: UnitOfWork = Depends(get_unit_of_work)) -> UserService:
    return UserService(uow)
