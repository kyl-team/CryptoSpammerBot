from core.job import current, JobPhase, storage
from database import Channel, Account, Proxy


async def start():
    current.clear()

    channels: set[str] = set()

    async for channel in Channel.find():
        channels.add(channel['url'])

    accounts = await Account.find().to_list()
    proxies = await Proxy.find().to_list()

    if storage.similar:
        current.phase = JobPhase.SIMILAR

    print(storage)
