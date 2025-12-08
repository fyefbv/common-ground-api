from fastapi import APIRouter

from app.api.endpoints import (
    auth_router,
    interests_router,
    profiles_router,
    users_router,
)

api_router = APIRouter(prefix="/api")

api_router.include_router(users_router)
api_router.include_router(auth_router)
api_router.include_router(profiles_router)
api_router.include_router(interests_router)
