from beanie import Document


class Account(Document):
    username: str | None
    user_id: int
    phone: str
    session: str
