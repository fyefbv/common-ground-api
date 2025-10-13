import uvicorn
from fastapi import FastAPI

from app.core.logger import app_logger
from app.core.exception_handlers import setup_exception_handlers


app = FastAPI(title="Common Ground API")

setup_exception_handlers(app)

if __name__ == "__main__":
    app_logger.info("🚀 Запуск приложения...")
    uvicorn.run(app="main:app", host="0.0.0.0", port=8000, reload=True)