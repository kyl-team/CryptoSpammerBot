import asyncio
import random
import re

from pydantic import BaseModel
from pyrofork import Client
from pyrofork.raw import functions
from pyrofork.raw.functions.channels import GetChannelRecommendations
from pyrofork.raw.types import UserFull
from pyrofork.raw.types.messages import ChatsSlice

from core.job import storage
from database import Channel, Account, Proxy


def chunks(arr: list, size: int):
    return [arr[i:i + size] for i in range(0, len(arr), size)]


async def get_similar_channels(client: Client, channels: list[str]) -> list[str]:
    arr = []
    for channel in channels:
        similar: ChatsSlice = await client.invoke(
            GetChannelRecommendations(channel=await client.resolve_peer(channel)))
        arr += [item.username for item in similar.chats]
    return arr


dictionary: dict[str, list[str]] = {
    'о': ['o', '0'],
    'с': ['c'],
    'з': ['3'],
    'а': ['a'],
    'р': ['p'],
    'в': ['8'],
    'х': ['x']
}


def obfuscate_text(text: str):
    words = text.split()
    for word in words:
        if random.random() > 0.5:
            source = random.choice(list(dictionary.keys()))
            new_word = word.replace(source, random.choice(dictionary[source]))
            text.replace(word, new_word, 1)
    return text


peer_pattern = re.compile(r'@([a-z0-9A-Z]+)')


class WorkResult(BaseModel):
    channels: list[str] = []
    users: list[str] = []


async def work(client: Client, channels: list[str]) -> None:
    result = WorkResult()

    for channel in channels:
        channel_chat = await client.join_chat(channel)
        await channel_chat.join()
        linked = channel_chat.linked_chat
        await linked.join()
        members = []
        async for member in linked.get_members():
            members.append(member)

        for member in members:
            user: UserFull = await client.invoke(
                functions.users.GetFullUser(id=await client.resolve_peer(member.user.id)))
            occurrences = peer_pattern.findall(user.about)

            for occurrence in occurrences:
                discussion = await client.get_chat(occurrence)

                async for discussion_member in discussion.get_members():
                    await client.send_message(discussion_member.user.id, obfuscate_text(storage.message.text))


async def start():
    channels: set[str] = set()

    async for channel in Channel.find():
        channels.add(channel['url'])

    proxies = await Proxy.find().to_list()
    clients = []

    proxy_index = 0

    async for account in Account.find():
        proxy = proxies[proxy_index % len(proxies)]
        proxy_data = {
            'scheme': 'http',
            'hostname': proxy.hostname,
            'port': proxy.port,
            'username': proxy.username,
            'password': proxy.password,
        }
        clients.append(Client(
            name=account.phone,
            proxy=proxy_data,
            session_string=account.session,
            in_memory=True
        ))
        proxy_index += 1

    if storage.similar:
        channel_chunks = chunks(list(channels), len(clients))

        tasks = []
        for i in range(len(clients)):
            tasks.append(get_similar_channels(clients[i], channel_chunks[i]))

        channel_groups = await asyncio.gather(*tasks)

        for group in channel_groups:
            for channel in group:
                channels.add(channel)

    channels_for_clients = chunks(list(channels), len(clients))

    tasks = []
    for i in range(len(clients)):
        tasks.append(work(clients[i], channels_for_clients[i]))

    await asyncio.gather(*tasks)
