from typing import Annotated

from beanie import Document, Indexed


class Account(Document):
    username: str | None
    user_id: Annotated[int, Indexed(unique=True)]
    phone: str
    session: str
