import re

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import channel_services, Channel

menu_router = Router()


@menu_router.callback_query(F.data.regexp(re.compile(r'^sources(_(clear))?$')).as_('match'))
async def menu(query: CallbackQuery, match: re.Match[str]):
    action = match.group(2)
    if action == 'clear':
        await Channel.find().delete()
        await query.answer('✅ Каналы очищены')

    loaded_text = ''
    builder = InlineKeyboardBuilder()
    i = 1

    for service in channel_services:
        count = await Channel.find(Channel.service == service).count()
        loaded_text += f'    <b>{service}</b>: <code>{count}</code>\n'
        builder.button(text=f'{i}. {service}', callback_data=f'sources_update_{service}')
        i += 1

    builder.button(text='🗑️ Очистить список каналов', callback_data='sources_clear')

    builder.button(text='🔙 Назад', callback_data='start')

    builder.adjust(*[1] * len(channel_services), 1)

    try:
        await query.message.edit_text('<b>Управление каналами</b>\n'
                                      '\n'
                                      '⬇️ Загружено:\n'
                                      f'{loaded_text}'
                                      f'\n'
                                      f'<b>Выберите сервис для обновления каналов</b>',
                                      reply_markup=builder.as_markup())
    except TelegramBadRequest:
        pass
