from uuid import UUID

from pydantic import BaseModel


class ProfileInterestBase(BaseModel):
    ids: set[UUID]


class ProfileInterestAdd(ProfileInterestBase):
    pass


class ProfileInterestDelete(ProfileInterestBase):
    pass
