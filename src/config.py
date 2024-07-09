from pydantic import BaseModel

from lib.storage import BaseStorage


class TelegramBotConfig(BaseModel):
    token: str = ''
    whitelist: list[int] = []


class DatabaseConfig(BaseModel):
    url: str = 'mongodb://localhost:27017/'
    name: str = 'crypto_bot'


class SessionConfig(BaseModel):
    api_id: str = ''
    api_hash: str = ''


class ServiceConfig(BaseStorage):
    telegram_bot: TelegramBotConfig = TelegramBotConfig()
    session: SessionConfig = SessionConfig()
    database: DatabaseConfig = DatabaseConfig()

    @property
    def pathname(self):
        return 'data/config.json'


config = ServiceConfig()
