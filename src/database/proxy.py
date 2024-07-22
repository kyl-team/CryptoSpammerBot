import re
from datetime import datetime
from typing import Literal

import aiohttp
from beanie import Document
from pydantic import Field

proxy_pattern = re.compile(
    r'^((https?)://)?((\w+):(\w+)@)?((((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){4})|[\w.]+):(\d|[1-9]\d{1,3}|[1-5]\d{4}|6[0-4]\d{3}|65[0-4]\d{2}|655[0-2]\d|6553[0-5])$')


class Proxy(Document):
    protocol: Literal['http', 'https']
    username: str | None
    password: str | None
    hostname: str
    port: int = Field(ge=0, lt=65536)
    timestamp: datetime = Field(default_factory=datetime.now)

    @property
    def require_auth(self) -> bool:
        return self.username and self.password is not None

    @property
    def with_hidden_credentials(self) -> str:
        if self.require_auth:
            return f'{self.protocol}://{self.username}:{self.password[:3]}***@{self.hostname}:{self.port}'
        else:
            return str(self)

    def __str__(self) -> str:
        if self.require_auth:
            return f'{self.protocol}://{self.username}:{self.password}@{self.hostname}:{self.port}'
        else:
            return f'{self.protocol}://{self.hostname}:{self.port}'

    @staticmethod
    def from_match(match: re.Match[str]) -> "Proxy":
        protocol, username, password, hostname, port = match.group(2, 4, 5, 6, 11)
        return Proxy(protocol=protocol, username=username, password=password, hostname=hostname, port=port)

    async def check_connection(self) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request('GET', 'https://httpbin.org/get', proxy=str(self)) as response:
                    return response.status == 200
        except Exception:
            return False
