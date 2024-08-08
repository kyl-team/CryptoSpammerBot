from typing import Any

from pydantic import BaseModel


class UserResult(BaseModel):
    id: int
    username: str | None
    phone: str | None
    first_name: str | None
    last_name: str | None


class UserChatResult(BaseModel):
    username: str
    members: list[UserResult] = []


class ChannelUserResult(UserResult):
    bio: str | None = None
    chats: list[UserChatResult] = []


class ChannelResult(BaseModel):
    id: int
    name: str
    has_linked_chat: bool
    client_name: str
    client_proxy: dict[str, Any]
    members: list[ChannelUserResult] = []
    errors: list[str]


WorkResult = list[ChannelResult]
