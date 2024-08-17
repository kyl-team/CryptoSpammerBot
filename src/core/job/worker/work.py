import asyncio
import logging
import re
from contextlib import suppress
from typing import Any

from pyrofork import Client
from pyrofork.enums import ChatType
from pyrofork.errors import FloodWait
from pyrofork.raw import functions
from pyrofork.raw.core import TLObject
from pyrofork.raw.functions.channels import GetChannelRecommendations
from pyrofork.raw.types import UserFull
from pyrofork.raw.types.messages import ChatsSlice
from pyrofork.types import Chat

from .report import WorkResult, ChannelResult, ChatResult, UserResult
from .state import TaskState
from .utils import obfuscate_text, format_exception
from .. import storage


async def safe_invoke(client: Client, query: TLObject, *args, **kwargs) -> Any:
    while True:
        try:
            return await client.invoke(query, *args, **kwargs)
        except FloodWait as e:
            await asyncio.sleep(e.value)


async def get_similar_channels(client: Client, channels: list[str]) -> list[str]:
    arr = []
    for channel in channels:
        with suppress(Exception):
            similar: ChatsSlice = await safe_invoke(client,
                                                    GetChannelRecommendations(
                                                        channel=await client.resolve_peer(channel)))
            arr += [item.username for item in similar.chats]
    return arr


async def get_bio(client: Client, user_id: int) -> str | None:
    user: Any = await safe_invoke(client,
                                  functions.users.GetFullUser(id=await client.resolve_peer(user_id)))
    user: UserFull = user.full_user

    return user.about


peer_pattern = re.compile(r'(@|t\.me/)(\w+)')


async def handle_discussion(client: Client, discussion: Chat, state: TaskState, chat_result: ChatResult) -> None:
    if discussion.id in state.known_discussions:
        return

    logging.info(discussion.id)
    logging.info(state.known_discussions)

    state.known_discussions.add(discussion.id)

    await state.set_state('получение мемберов')
    members = []
    try:
        async for member in discussion.get_members():
            if state.stop_signal:
                break
            if member.user.is_bot:
                continue
            members.append(member)
            await state.set_state(f'получение мемберов ({len(members)}/?)')
    except Exception as e:
        chat_result.errors.append(
            f'Не удалось получить список участников чата @{discussion.username} [{discussion.id}]. {format_exception(e)}')

    for k in range(len(members)):
        if state.stop_signal:
            break
        member = members[k]
        await state.set_state(f'обработка мембера ({k}/{len(members)})')
        try:
            bio = await get_bio(client, member.user.id)
        except Exception as e:
            chat_result.errors.append(
                f'Не удалось получить информацию по участнику @{member.user.username} [{member.user.id}]. {format_exception(e)}')
            continue

        user_result = UserResult(id=member.user.id, username=member.user.username,
                                 phone=member.user.phone_number,
                                 first_name=member.user.first_name, last_name=member.user.last_name,
                                 bio=bio)
        chat_result.members.append(user_result)

        if not bio:
            return

        occurrences = peer_pattern.findall(bio)

        await state.set_state(f'поиск по мемберу ({k}/{len(members)})')

        if len(occurrences) > 0 and not storage.draft:
            try:
                await client.send_message(member.user.id,
                                          obfuscate_text(storage.message.text))
            except Exception as e:
                chat_result.errors.append(
                    f'Не удалось написать участнику @{member.user.username} [{member.user.id}]. {format_exception(e)}')

        for occurrence in occurrences:
            if state.stop_signal:
                break
            occurrence = occurrence[1]  # 2nd match group

            await state.set_state(f'поиск по мемберу ({k}/{len(members)}) | получение чата @{occurrence}')

            try:
                new_discussion = await client.get_chat(occurrence)
            except Exception as e:
                chat_result.errors.append(
                    f'Не удалось получить пользовательский чат @{occurrence} пользователя'
                    f' @{member.user.username} [{member.user.id}]. {format_exception(e)}')
                continue

            if new_discussion.type == ChatType.CHANNEL:
                if new_discussion.linked_chat:
                    new_discussion = new_discussion.linked_chat
                else:
                    continue

            user_chat = ChatResult(username=occurrence, id=new_discussion.id, depth=chat_result.depth + 1)
            user_result.chats.append(user_chat)

            await handle_discussion(client, new_discussion, state, user_chat)


async def work(client: Client, channels: list[str], state: TaskState) -> WorkResult:
    results: WorkResult = []
    for channel in channels:
        if state.stop_signal:
            break
        await state.start_channel()

        channel_result = ChannelResult(id=-1, name=channel,
                                       client_name=client.name, client_proxy=client.proxy)
        results.append(channel_result)

        try:
            channel_chat = await client.get_chat(channel)
        except Exception as e:
            channel_result.errors.append(
                f'Ошибка получения канала @{channel}. {format_exception(e)}')
            continue

        channel_result.id = channel_chat.id

        if channel_chat.linked_chat:
            channel_result.linked_chat = ChatResult(username=channel_chat.linked_chat.username,
                                                    id=channel_chat.linked_chat.id)
            if not storage.draft:
                await state.set_state('вход в беседу')
                try:
                    await channel_chat.linked_chat.join()
                except Exception as e:
                    channel_result.errors.append(
                        f'Не удалось зайти в чат канала. {format_exception(e)}')

            await handle_discussion(client, channel_chat.linked_chat, state, channel_result.linked_chat)
    return results
