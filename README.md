# CommonGround API

> 🚀 Backend-репозиторий для приложения CommonGround — платформы для тематического общения и нетворкинга.

Это ядро приложения, отвечающее за всю бизнес-логику, работу с данными и обеспечение реального-времени взаимодействия между клиентами.

## 🛠 Технологический стек

*   **Фреймворк:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11+)
*   **База данных:** [PostgreSQL](https://www.postgresql.org/) с [SQLAlchemy](https://www.sqlalchemy.org/) ORM, [asyncpg](https://magicstack.github.io/asyncpg/) и [Alembic](https://alembic.sqlalchemy.org/) для миграций
*   **Реальное время:** [WebSocket](https://fastapi.tiangolo.com/advanced/websockets/) для чат-рулетки и уведомлений
*   **Кэширование:** [Redis](https://redis.io/) для очередей и быстрого доступа к данным
*   **Аутентификация:** [JWT](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)
*   **Документация:** Автоматическая генерация OpenAPI/Swagger (`/docs`)

## 🌟 Ключевые функции API

*   **Тематическая чат-рулетка:** Алгоритм подбора собеседников на основе общих интересов.
*   **Управление тематическими комнатами:** CRUD для групповых чатов и сообществ.
*   **Система пользователей и интересов:** Регистрация, аутентификация, профили.
*   **Real-time уведомления:** Мгновенные оповещения о новых сообщениях и событиях.
*   **RESTful & WebSocket API:** Полностью асинхронное и высокопроизводительное API.

## 📦 Быстрый старт

1.  Клонируйте репозиторий:
    ```bash
    git clone https://github.com/fyefbv/commonground-api.git
    cd commonground-api
    ```

2.  Установите зависимости:
    ```bash
    pip install -r requirements.txt
    ```

3.  Запустите сервер для разработки:
    ```bash
    uvicorn app.main:app --reload
    ```

API будет доступно на `http://localhost:8000`, а интерактивная документация — на `http://localhost:8000/docs`.

---

**Клиентская часть:** ➡️ [commonground-android](https://github.com/fyefbv/commonground-android)