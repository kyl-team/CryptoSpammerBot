from pyrogram import Client

from config import config

loaded_clients: dict[str, Client] = {}


def get_client(phone: str, **kwargs) -> Client | None:
    if phone not in loaded_clients:
        client = Client(phone, api_id=config.session.api_id, api_hash=config.session.api_hash, phone_number=phone,
                        in_memory=True, **kwargs)
        loaded_clients[phone] = client

    return loaded_clients[phone]
