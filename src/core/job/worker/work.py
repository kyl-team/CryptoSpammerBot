import asyncio
import re
from typing import Any

from pyrofork import Client
from pyrofork.raw import functions
from pyrofork.raw.functions.channels import GetChannelRecommendations
from pyrofork.raw.types import UserFull
from pyrofork.raw.types.messages import ChatsSlice
from pyrofork.types import Chat

from core.job import storage
from .report import WorkResult, UserChatResult, ChannelUserResult, \
    ChannelResult
from .state import TaskState
from .utils import obfuscate_text


async def get_similar_channels(client: Client, channels: list[str]) -> list[str]:
    arr = []
    for channel in channels:
        similar: ChatsSlice = await client.invoke(
            GetChannelRecommendations(channel=await client.resolve_peer(channel)))
        arr += [item.username for item in similar.chats]
    return arr


peer_pattern = re.compile(r'(@|t\.me/)(\w+)')


async def handle_discussion(client: Client, discussion: Chat, state: TaskState, channel_result: ChannelResult):
    state.known_discussions.add(discussion.username)
    await state.set_state('получение мемберов')
    members = []
    try:
        async for member in discussion.get_members():
            if member.user.is_bot:
                continue
            members.append(member)
            await state.set_state(f'получение мемберов ({len(members)}/?)')
    except Exception:
        channel_result.errors.append(
            f'Не удалось получить список участников чата @{discussion.username} [{discussion.id}]')

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
            channel_result.errors.append(
                f'Не удалось получить информацию по участнику @{member.user.username} [{member.user.id}]')
            continue

        await state.set_state(f'поиск по мемберу ({k}/{len(members)})')

        if len(occurrences) > 0:
            try:
                await client.send_message(member.user.id,
                                          obfuscate_text(storage.message.text))
            except Exception:
                channel_result.errors.append(
                    f'Не удалось написать участнику @{member.user.username} [{member.user.id}]')

        for occurrence in occurrences:
            if occurrence in state.known_discussions:
                continue

            occurrence = occurrence[1]  # 2nd match group
            await state.set_state(f'поиск по мемберу ({k}/{len(members)}) | получение чата @{occurrence}')
            try:
                new_discussion = await client.get_chat(occurrence)

                user_chat = UserChatResult(username=occurrence)
                user_result.chats.append(user_chat)
            except Exception:
                channel_result.errors.append(
                    f'Не удалось получить пользовательский чат @{occurrence} пользователя'
                    f' @{member.user.username} [{member.user.id}]')
                continue
            await handle_discussion(client, new_discussion, state, channel_result)


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

            await handle_discussion(client, channel_chat, state, channel_result)
        await asyncio.sleep(5)
    return results
