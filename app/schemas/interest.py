from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class InterestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str


class InterestBatch(BaseModel):
    interest_ids: list[UUID] = Field(..., min_length=1, max_length=50)
