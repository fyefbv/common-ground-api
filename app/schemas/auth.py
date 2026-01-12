from uuid import UUID

from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str


class TokenRefresh(BaseModel):
    token: str


class ProfileTokenCreate(BaseModel):
    profile_id: UUID
