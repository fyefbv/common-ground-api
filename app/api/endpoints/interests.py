from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_interest_service
from app.schemas.user import InterestResponse
from app.services.user import InterestService

interests_router = APIRouter(prefix="/interests", tags=["Интересы"])


@interests_router.get("/", response_model=list[InterestResponse])
async def get_interests(
    interest_service: InterestService = Depends(get_interest_service),
    _: UUID = Depends(get_current_user),
) -> list[InterestResponse]:
    return await interest_service.get_interests()
