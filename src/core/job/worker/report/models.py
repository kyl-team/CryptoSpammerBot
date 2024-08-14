from typing import Any

from pydantic import BaseModel


class ChatResult(BaseModel):
    id: int
    username: str | None
    members: list["UserResult"] = []
    errors: list[str] = []
    depth: int = 0


class UserResult(BaseModel):
    id: int
    username: str | None
    phone: str | None
    first_name: str | None
    last_name: str | None
    bio: str | None
    chats: list[ChatResult] = []


class ChannelResult(BaseModel):
    id: int
    name: str
    client_name: str
    client_proxy: dict[str, Any] | None
    linked_chat: ChatResult | None = None
    errors: list[str] = []


WorkResult = list[ChannelResult]
