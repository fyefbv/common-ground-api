from app.db.models.chat_roulette_message import ChatRouletteMessage
from app.repositories.base import Repository


class ChatRouletteMessageRepository(Repository):
    model = ChatRouletteMessage
