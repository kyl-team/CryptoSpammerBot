import asyncio
import random
import re
from datetime import datetime
from typing import Any

from aiogram.types import BufferedInputFile
from pydantic import BaseModel
from pyrofork import Client
from pyrofork.raw import functions
from pyrofork.raw.functions.channels import GetChannelRecommendations
from pyrofork.raw.types import UserFull
from pyrofork.raw.types.messages import ChatsSlice

from bot import bot
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
    words = []
    for word in text.split():
        if random.random() > 0.5:
            source = random.choice(list(dictionary.keys()))
            new_word = word.replace(source, random.choice(dictionary[source]))
            print(new_word)
            words.append(new_word)
        else:
            words.append(word)
    return ' '.join(words)


peer_pattern = re.compile(r'@(\w+)')


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


WorkResult = list[ChannelResult]


async def work(client: Client, channels: list[str]) -> WorkResult:
    results: WorkResult = []
    for channel in channels:
        channel_chat = await client.get_chat(channel)
        channel_result = ChannelResult(id=channel_chat.id, name=channel, has_linked_chat=bool(channel_chat.linked_chat),
                                       client_name=client.name, client_proxy=client.proxy)
        if channel_chat.linked_chat:
            await channel_chat.linked_chat.join()
            members = []
            async for member in channel_chat.linked_chat.get_members():
                if not member.user.is_bot:
                    members.append(member)

            for member in members:
                user: Any = await client.invoke(
                    functions.users.GetFullUser(id=await client.resolve_peer(member.user.id)))
                user: UserFull = user.full_user

                user_result = ChannelUserResult(id=member.user.id, username=member.user.username,
                                                phone=member.user.phone_number,
                                                first_name=member.user.first_name, last_name=member.user.last_name,
                                                bio=user.about)
                channel_result.members.append(user_result)

                occurrences = peer_pattern.findall(user.about)

                for occurrence in occurrences:
                    discussion = await client.get_chat(occurrence)

                    user_chat = UserChatResult(username=occurrence)
                    user_result.chats.append(user_chat)

                    async for discussion_member in discussion.get_members():
                        user_chat.members.append(
                            UserResult(id=discussion_member.user.id, username=discussion_member.user.username,
                                       phone=discussion_member.user.phone_number,
                                       first_name=discussion_member.user.first_name,
                                       last_name=discussion_member.user.last_name))
                        await client.send_message(discussion_member.user.id, obfuscate_text(storage.message.text))
        results.append(channel_result)
    return results


async def start(user_id: int):
    channels: set[str] = set()

    async for channel in Channel.find():
        channels.add(channel.url)

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
        client = Client(
            name=account.phone,
            proxy=proxy_data,
            session_string=account.session,
            in_memory=True
        )
        clients.append(client)
        await client.connect()
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

    results_arr = await asyncio.gather(*tasks)
    results: list[ChannelResult] = []
    for result_items in results_arr:
        results += result_items

    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    markdown_content = f'# Отчет о работе {timestamp}\n'

    markdown_content += '## По каналам\n'

    for result in results:
        markdown_content += f'## Канал @{result.name} [{result.id}], беседа: {"есть" if result.has_linked_chat else "нет"}\n\n'
        markdown_content += f'Обработчик: {result.client_name}, прокси: {result.client_proxy["hostname"]}:{result.client_proxy["port"]}\n\n'
        markdown_content += '### Участники\n'
        i = 0
        for member in result.members:
            markdown_content += f'{i}. @{member.username} ({member.first_name} {member.last_name}), телефон: {member.phone}, био: "{member.bio}", найдено бесед: {len(member.chats)} [{member.id}]\n'
            for chat in member.chats:
                markdown_content += f'    Беседа @{chat.username}, участников: {len(chat.members)}\n'
                j = 0
                for chat_member in chat.members:
                    markdown_content += f'        {j}. Участник @{chat_member.username} ({chat_member.first_name} {chat_member.last_name}), телефон: {chat_member.phone} [{chat_member.id}]\n'
                    j += 1
            i += 1

    report = BufferedInputFile(markdown_content.encode(),
                               filename=f"report.md")
    await bot.send_document(user_id, report, caption=f'Отчет от {timestamp}')
