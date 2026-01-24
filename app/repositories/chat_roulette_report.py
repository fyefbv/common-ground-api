from app.db.models.chat_roulette_report import ChatRouletteReport
from app.repositories.base import Repository


class ChatRouletteReportRepository(Repository):
    model = ChatRouletteReport
