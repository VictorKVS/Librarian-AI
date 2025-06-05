# telegram/bot.py
from core.adapters.telegram_adapter import TelegramAdapter

class TelegramBot:
    def __init__(self, token: str):
        self.adapter = TelegramAdapter(token)

    async def start(self):
        # TODO: инициализация и запуск поллинга или webhook
        pass

    async def handle_update(self, update):
        # TODO: логика обработки входящего сообщения
        pass