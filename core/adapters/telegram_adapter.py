# core/adapters/telegram_adapter.py
class TelegramAdapter:
    def __init__(self, bot_token: str):
        self.bot_token = bot_token

    async def send_message(self, chat_id: int, text: str):
        # TODO: вызывать API Telegram
        raise NotImplementedError("TelegramAdapter.send_message not implemented")