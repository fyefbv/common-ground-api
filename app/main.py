import uvicorn
from fastapi import FastAPI

from core.logger import app_logger


app = FastAPI(title="Common Ground API")

if __name__ == "__main__":
    app_logger.info("🚀 Запуск приложения...")
    uvicorn.run(app="main:app", host="0.0.0.0", port=8000, reload=True)