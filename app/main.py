import uvicorn
from fastapi import FastAPI

from app.api.routers import api_router, ws_router
from app.core.exception_handlers import setup_exception_handlers
from app.core.logger import app_logger

app = FastAPI(
    title="Common Ground API",
    description="API для чат-рулетки, управления комнатами и профилями пользователей. Поддерживает аутентификацию, работу с интересами, загрузку аватарок и WebSocket-уведомления.",
    version="1.0.0",
    openapi_tags=[
        {
            "name": "Аутентификация",
            "description": "Регистрация, вход, обновление токенов",
        },
        {
            "name": "Чат-рулетка",
            "description": "Поиск партнёров, сессии, сообщения и статистика",
        },
        {"name": "Интересы", "description": "Список доступных интересов для профилей"},
        {
            "name": "Профили",
            "description": "Создание и управление профилями пользователей, интересы, аватарки",
        },
        {
            "name": "Комнаты",
            "description": "Создание комнат, управление участниками, сообщения",
        },
        {
            "name": "Пользователи",
            "description": "Управление учётными записями пользователей",
        },
        {"name": "WebSocket: Комнаты", "description": "WebSocket для чата в комнатах"},
        {"name": "WebSocket: Чат-рулетка", "description": "WebSocket для чат-рулетки"},
    ],
)

setup_exception_handlers(app)

app.include_router(api_router)
app.include_router(ws_router)

if __name__ == "__main__":
    app_logger.info("🚀 Запуск приложения...")
    uvicorn.run(app="main:app", host="0.0.0.0", port=8000, reload=True)
