from uuid import UUID

from pydantic import BaseModel, ConfigDict


class InterestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
