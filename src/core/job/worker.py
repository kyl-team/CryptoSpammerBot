import asyncio

from pyrofork import Client
from pyrofork.raw.functions.channels import GetChannelRecommendations
from pyrofork.raw.types.messages import ChatsSlice
from yarl import URL

from core.job import current, JobPhase, storage
from database import Channel, Account, Proxy


def __chunks(arr: list, size: int):
    for i in range(0, len(arr), size):
        yield arr[i:i + size]


def chunks(arr: list, size: int) -> list:
    return list(__chunks(arr, size))


async def get_similar_channels(client: Client, channels: list[str]) -> list[str]:
    arr = []
    for channel in channels:
        similar: ChatsSlice = await client.invoke(
            GetChannelRecommendations(channel=await client.resolve_peer(channel)))
        arr += [item.username for item in similar.chats]
    return arr


async def start():
    current.clear()

    channels: set[str] = set()

    async for channel in Channel.find():
        channels.add(channel['url'])

    proxies = await Proxy.find().to_list()
    clients = []

    proxy_index = 0

    async for account in Account.find():
        proxy = proxies[proxy_index % len(proxies)]
        proxy_url = URL('http://' + proxy.url)
        proxy_data = {
            'scheme': 'http',
            'hostname': proxy_url.host,
            'port': proxy_url.port,
            'username': proxy_url.user,
            'password': proxy_url.password,
        }
        clients.append(Client(
            name=account.phone,
            proxy=proxy_data,
            session_string=account.session,
            in_memory=True
        ))
        proxy_index += 1

    if storage.similar:
        current.phase = JobPhase.SIMILAR

        channel_chunks = chunks(list(channels), len(clients))

        tasks = []
        for i in range(len(clients)):
            tasks.append(get_similar_channels(clients[i], channel_chunks[i]))

        channel_groups = await asyncio.gather(*tasks)

        for group in channel_groups:
            for channel in group:
                channels.add(channel)

    print('Total', len(channels), 'channels')
