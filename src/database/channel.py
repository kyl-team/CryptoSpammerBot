from datetime import datetime
from typing import Literal, Annotated

from beanie import Document, Indexed
from pydantic import Field

channel_services = ['tgstat.ru', 'telemetr.io', 'telemetr.me']
ChannelService = Literal['tgstat.ru', 'telemetr.io', 'telemetr.me']


class Channel(Document):
    url: Annotated[str, Indexed(unique=True)]
    service: Annotated[ChannelService, Indexed()]
    timestamp: datetime = Field(default_factory=datetime.now)
