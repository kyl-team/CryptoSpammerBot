from beanie import Document, PydanticObjectId


class Account(Document):
    username: str | None
    user_id: int
    phone: str
    session: str
    proxy_id: PydanticObjectId
