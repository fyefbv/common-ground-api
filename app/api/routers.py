from fastapi import APIRouter

from app.api.endpoints.auth import auth_router
from app.api.endpoints.interests import interests_router
from app.api.endpoints.profiles import profiles_router
from app.api.endpoints.users import users_router

api_router = APIRouter()

api_router.include_router(users_router)
api_router.include_router(auth_router)
api_router.include_router(profiles_router)
api_router.include_router(interests_router)
