from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from config import config
from .account import Account
from .channel import Channel, ChannelService, channel_services
from .proxy import Proxy

client = AsyncIOMotorClient(config.database.url)
database = client[config.database.name]


async def connect():
    return await init_beanie(database=database, document_models=[Proxy, Account, Channel])
