import asyncio
import re
from typing import Any

from pyrofork import Client
from pyrofork.errors import RPCError
from pyrofork.raw import functions
from pyrofork.raw.functions.channels import GetChannelRecommendations
from pyrofork.raw.types import UserFull
from pyrofork.raw.types.messages import ChatsSlice
from pyrofork.types import Chat

from .report import WorkResult, ChannelResult, ChatResult, UserResult
from .state import TaskState


async def get_similar_channels(client: Client, channels: list[str]) -> list[str]:
    arr = []
    for channel in channels:
        similar: ChatsSlice = await client.invoke(
            GetChannelRecommendations(channel=await client.resolve_peer(channel)))
        arr += [item.username for item in similar.chats]
    return arr


async def get_bio(client: Client, user_id: int) -> str | None:
    user: Any = await client.invoke(
        functions.users.GetFullUser(id=await client.resolve_peer(user_id)))
    user: UserFull = user.full_user

    return user.about


peer_pattern = re.compile(r'(@|t\.me/)(\w+)')


async def handle_discussion(client: Client, discussion: Chat, state: TaskState, chat_result: ChatResult):
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
        chat_result.errors.append(
            f'Не удалось получить список участников чата @{discussion.username} [{discussion.id}]')

    for k in range(len(members)):
        member = members[k]
        await state.set_state(f'обработка мембера ({k}/{len(members)})')
        try:
            bio = await get_bio(client, member.user.id)

            user_result = UserResult(id=member.user.id, username=member.user.username,
                                     phone=member.user.phone_number,
                                     first_name=member.user.first_name, last_name=member.user.last_name,
                                     bio=bio)
            chat_result.members.append(user_result)

            occurrences = peer_pattern.findall(bio)
        except Exception:
            chat_result.errors.append(
                f'Не удалось получить информацию по участнику @{member.user.username} [{member.user.id}]')
            continue

        await state.set_state(f'поиск по мемберу ({k}/{len(members)})')

        if len(occurrences) > 0:
            try:
                pass
                # await client.send_message(member.user.id,
                #                           obfuscate_text(storage.message.text))
            except Exception:
                chat_result.errors.append(
                    f'Не удалось написать участнику @{member.user.username} [{member.user.id}]')

        for occurrence in occurrences:
            occurrence = occurrence[1]  # 2nd match group

            if occurrence in state.known_discussions:
                continue

            await state.set_state(f'поиск по мемберу ({k}/{len(members)}) | получение чата @{occurrence}')

            try:
                new_discussion = await client.get_chat(occurrence)

                user_chat = ChatResult(username=occurrence, id=new_discussion.id, depth=chat_result.depth + 1)
                user_result.chats.append(user_chat)
            except Exception:
                chat_result.errors.append(
                    f'Не удалось получить пользовательский чат @{occurrence} пользователя'
                    f' @{member.user.username} [{member.user.id}]')
                continue

            await handle_discussion(client, new_discussion, state, user_chat)


async def work(client: Client, channels: list[str], state: TaskState) -> WorkResult:
    results: WorkResult = []
    for channel in channels:
        await state.start_channel()

        channel_result = ChannelResult(id=-1, name=channel,
                                       client_name=client.name, client_proxy=client.proxy)
        results.append(channel_result)

        try:
            channel_chat = await client.get_chat(channel)
        except RPCError as e:
            channel_result.errors.append(f'Ошибка получения канала @{channel}, ответ: {e.ID or e.NAME}')
            continue
        except Exception as e:
            channel_result.errors.append(f'Неизвестная ошибка получения канала @{channel}, {type(e).__name__}')
            continue

        if channel_chat.linked_chat:
            channel_result.linked_chat = ChatResult(username=channel_chat.linked_chat.username,
                                                    id=channel_chat.linked_chat.id)
            await state.set_state('вход в беседу')
            try:
                await channel_chat.linked_chat.join()
            except Exception:
                channel_result.errors.append(f'Не удалось зайти в чат канала')

            await handle_discussion(client, channel_chat, state, channel_result.linked_chat)
        await asyncio.sleep(5)
    return results
