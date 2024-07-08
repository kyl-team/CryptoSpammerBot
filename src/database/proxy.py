from datetime import datetime

from beanie import Document
from pydantic import Field


class Proxy(Document):
    url: str
    timestamp: datetime = Field(default_factory=datetime.now)
