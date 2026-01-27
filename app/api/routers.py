from fastapi import APIRouter

from app.api.endpoints import (
    auth_router,
    chat_roulette_router,
    interests_router,
    profiles_router,
    rooms_router,
    users_router,
)
from app.api.websockets.room_chat import ws_rooms_router
from app.api.websockets.roulette_chat import ws_chat_roulette_router

api_router = APIRouter(prefix="/api")
ws_router = APIRouter(prefix="/ws")

api_router.include_router(users_router)
api_router.include_router(auth_router)
api_router.include_router(profiles_router)
api_router.include_router(interests_router)
api_router.include_router(rooms_router)
api_router.include_router(chat_roulette_router)

ws_router.include_router(ws_rooms_router)
ws_router.include_router(ws_chat_roulette_router)
