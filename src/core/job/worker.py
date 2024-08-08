import asyncio
import random
import re
from datetime import datetime, timedelta
from typing import Any

from aiogram.types import BufferedInputFile, Message
from pydantic import BaseModel
from pyrofork import Client
from pyrofork.raw import functions
from pyrofork.raw.functions.channels import GetChannelRecommendations
from pyrofork.raw.types import UserFull
from pyrofork.raw.types.messages import ChatsSlice

from bot import bot
from core.job import storage
from database import Channel, Account, Proxy


def slice_array(arr: list, n: int):
    k, m = divmod(len(arr), n)
    slices = [arr[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n)]
    return slices


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


peer_pattern = re.compile(r'(@|t\.me/)(\w+)')


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
    errors: list[str]


class TaskState:
    def __init__(self, message: Message, total: int):
        self.message = message
        self.total = total
        self.progress = 0
        self.state = None
        self.last_print = None

    async def sync(self):
        if self.last_print is None or datetime.now() > self.last_print + timedelta(seconds=10):
            state_text = f", {self.state}" if self.state else ""
            await self.message.edit_text(f'⌛ Обработано: {self.progress}/{self.total}{state_text}')
            self.last_print = datetime.now()

    async def start_channel(self):
        self.progress += 1
        self.state = None
        await self.sync()

    async def set_state(self, state: str):
        self.state = state
        await self.sync()


WorkResult = list[ChannelResult]


async def work(client: Client, channels: list[str], state: TaskState) -> WorkResult:
    results: WorkResult = []
    for channel in channels:
        await state.start_channel()
        try:
            channel_chat = await client.get_chat(channel)
        except Exception:
            continue
        errors = []
        channel_result = ChannelResult(id=channel_chat.id, name=channel, has_linked_chat=bool(channel_chat.linked_chat),
                                       client_name=client.name, client_proxy=client.proxy, errors=errors)
        results.append(channel_result)

        if channel_chat.linked_chat:
            await state.set_state('вход в беседу')
            try:
                await channel_chat.linked_chat.join()
                await asyncio.sleep(3)
            except Exception:
                errors.append(f'Не удалось зайти в чат канала')

            await state.set_state('получение мемберов')
            members = []
            try:
                async for member in channel_chat.linked_chat.get_members():
                    if member.user.is_bot:
                        continue
                    members.append(member)
                    await state.set_state(f'получение мемберов ({len(members)})')
            except Exception:
                errors.append(
                    f'Не удалось получить список участников чата @{channel_chat.linked_chat.username} [{channel_chat.linked_chat.id}]')
                continue

            for k in range(len(members)):
                member = members[k]
                await state.set_state(f'обработка мембера ({k}/{len(members)})')
                try:
                    user: Any = await client.invoke(
                        functions.users.GetFullUser(id=await client.resolve_peer(member.user.id)))
                    user: UserFull = user.full_user

                    user_result = ChannelUserResult(id=member.user.id, username=member.user.username,
                                                    phone=member.user.phone_number,
                                                    first_name=member.user.first_name, last_name=member.user.last_name,
                                                    bio=user.about)
                    channel_result.members.append(user_result)

                    occurrences = peer_pattern.findall(user.about)
                except Exception:
                    errors.append(
                        f'Не удалось получить информацию по участнику @{member.user.username} [{member.user.id}]')
                    continue

                await state.set_state(f'поиск по мемберу ({k}/{len(members)})')

                for occurrence in occurrences:
                    occurrence = occurrence[1] # 2nd match group
                    await state.set_state(f'поиск по мемберу ({k}/{len(members)}) | получение чата @{occurrence}')
                    try:
                        discussion = await client.get_chat(occurrence)

                        user_chat = UserChatResult(username=occurrence)
                        user_result.chats.append(user_chat)
                    except Exception:
                        errors.append(
                            f'Не удалось получить пользовательский чат @{occurrence} пользователя'
                            f' @{member.user.username} [{member.user.id}]')
                        continue

                    await state.set_state(f'поиск по мемберу ({k}/{len(members)}) | обработка чата @{occurrence}')

                    try:
                        async for discussion_member in discussion.get_members():
                            if discussion_member.user.is_bot:
                                continue

                            user_chat.members.append(
                                UserResult(id=discussion_member.user.id, username=discussion_member.user.username,
                                           phone=discussion_member.user.phone_number,
                                           first_name=discussion_member.user.first_name,
                                           last_name=discussion_member.user.last_name))
                            await state.set_state(
                                f'поиск по мемберу ({k}/{len(members)}) | обработка чата (@{occurrence}) | отправка сообщения (@{discussion_member.user.username})')
                            try:
                                await client.send_message(discussion_member.user.id,
                                                          obfuscate_text(storage.message.text))
                            except Exception:
                                errors.append(
                                    f'Не удалось написать пользователю @{discussion_member.user.username} [{discussion_member.user.id}] (беседа @{discussion.username} [{discussion.id}])')
                                continue
                    except Exception:
                        errors.append(f'Не удалось получить мемберов дискуссии (@{discussion.username})')
        await asyncio.sleep(5)
    return results


async def start(user_id: int):
    channels: set[str] = set()

    async for channel in Channel.find():
        channels.add(channel.url)

    proxies = await Proxy.find().to_list()
    clients = []

    proxy_index = 0

    async for account in Account.find():
        if len(proxies) > 0:
            proxy = proxies[proxy_index % len(proxies)]
            proxy_data = {
                'scheme': 'http',
                'hostname': proxy.hostname,
                'port': proxy.port,
                'username': proxy.username,
                'password': proxy.password,
            }
        else:
            proxy_data = None
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
        channel_slices = slice_array(list(channels), len(clients))

        tasks = []
        for i in range(len(clients)):
            tasks.append(get_similar_channels(clients[i], channel_slices[i]))

        channel_groups = await asyncio.gather(*tasks)

        for group in channel_groups:
            for channel in group:
                channels.add(channel)

    channels_for_clients = slice_array(list(channels), len(clients))

    max_load = max(0, *[len(x) for x in channels_for_clients])
    if max_load > 20:
        await bot.send_message(user_id, f'⚠️ Максимальная нагрузка на аккаунт: {max_load} каналов')

    status_message = await bot.send_message(user_id, f'🤖 Задача в процессе')

    state = TaskState(status_message, len(channels))

    tasks = []
    for i in range(len(clients)):
        tasks.append(work(clients[i], channels_for_clients[i], state))

    results_arr = await asyncio.gather(*tasks)
    results: list[ChannelResult] = []
    for result_items in results_arr:
        results += result_items

    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    markdown_content = f'# Отчет о работе {timestamp}\n'

    for result in results:
        markdown_content += f'## Канал @{result.name} [{result.id}], беседа: {"есть" if result.has_linked_chat else "нет"}\n\n'
        markdown_content += f'Обработчик: {result.client_name}, прокси: {result.client_proxy["hostname"]}:{result.client_proxy["port"]}\n\n'

        if len(result.errors):
            markdown_content += '### Ошибки\n'
            for error in result.errors:
                markdown_content += f' * {error}\n'

        if len(result.members):
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
