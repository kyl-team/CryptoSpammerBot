import re

import aiohttp
from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bs4 import BeautifulSoup, Tag

from database import channel_services, ChannelService, Channel
from ..state_clear import get_state_clear_markup


async def update_channels(service: ChannelService, data: dict[str, ...] | None = None) -> int:
    match service:
        case 'tgstat.ru':
            channels: set[str] = set()
            async with aiohttp.ClientSession() as session:
                async with session.get('https://uk.tgstat.com/ratings/channels/crypto', headers={
                    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                    "accept-language": "en-US,en;q=0.9",
                    "cache-control": "max-age=0",
                    "priority": "u=0, i",
                    "sec-ch-ua": '"Chromium";v="124", "DuckDuckGo";v="124", "Not-A.Brand";v="99"',
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": '"Windows"',
                    "sec-fetch-dest": "document",
                    "sec-fetch-mode": "navigate",
                    "sec-fetch-site": "cross-site",
                    "sec-fetch-user": "?1",
                    "sec-gpc": "1",
                    "upgrade-insecure-requests": "1"
                }) as response:
                    text = await response.text()
                    bs4 = BeautifulSoup(text, 'html.parser')
                    card_holder = bs4.select_one('#sticky-center-column')
                    cards: list[Tag] = card_holder.find_all('div')
                    pattern = re.compile(r'https://uk\.tgstat\.com/channel/@(\w+)/stat')
                    for card in cards:
                        link_elements = card.find_all('a')
                        for link_element in link_elements:
                            if link_element and link_element.attrs:
                                url: str | None = link_element.attrs.get('href')
                                if url:
                                    match = pattern.match(url.strip())
                                    if match:
                                        channels.add(match.group(1))
            for channel in channels:
                document = Channel(url=channel, service=service)
                await document.insert()
            return len(channels)
        case 'telemetr.io':
            raise NotImplementedError('WIP')
        case 'telemetr.me':
            if not data or 'session_id' not in data:
                raise ValueError('Missing session_id')

            session_id = data['session_id']

            raise NotImplementedError('WIP')
        case _:
            raise ValueError(f'Unknown service: {service}')


update_router = Router()


class UpdateServiceStates(StatesGroup):
    php_session = State()


@update_router.callback_query(F.data.regexp(re.compile(r'sources_update_([a-z.]+)')).as_('match'))
async def update_source(query: CallbackQuery, match: re.Match[str], state: FSMContext):
    service = match.group(1)

    if service not in channel_services:
        return await query.answer('❌ Сервис не найден', show_alert=True)

    if service == 'telemetr.me':
        await state.set_state(UpdateServiceStates.php_session)
        return await query.message.edit_text('<b>Введите PHPSESSID</b>', reply_markup=get_state_clear_markup())

    await query.message.edit_text('⌛ Ожидайте')
    count = await update_channels(service)

    builder = InlineKeyboardBuilder()

    builder.button(text='🔙 Назад', callback_data='sources')

    await query.message.edit_text(f'✅ Успешно загружено {count} каналов!', reply_markup=builder.as_markup())


@update_router.message(StateFilter(UpdateServiceStates.php_session), F.text)
async def php_session(message: Message, state: FSMContext):
    await state.clear()

    status_message = await message.answer('⌛ Ожидайте')
    count = await update_channels('telemetr.me', {'session_id': message.text})

    builder = InlineKeyboardBuilder()

    builder.button(text='🔙 Назад', callback_data='sources')

    await status_message.edit_text(f'✅ Успешно загружено {count} каналов!', reply_markup=builder.as_markup())
