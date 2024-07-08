from datetime import datetime
from typing import Literal

from beanie import Document
from pydantic import Field

channel_services = ['tgstat.ru', 'telemetr.io', 'telemetr.me']
ChannelService = Literal['tgstat.ru', 'telemetr.io', 'telemetr.me']


class Channel(Document):
    url: str
    service: ChannelService
    timestamp: datetime = Field(default_factory=datetime.now)
