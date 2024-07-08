from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import channel_services, Channel

menu_router = Router()


@menu_router.callback_query(F.data == 'sources')
async def menu(query: CallbackQuery):
    loaded_text = ''
    builder = InlineKeyboardBuilder()
    i = 1

    for service in channel_services:
        loaded_text += f'    <b>{service}</b>: <code>{await Channel.find(Channel.service == service).count()}</code>\n'
        builder.button(text=f'{i}. {service}', callback_data=f'sources_update_{service}')
        i += 1

    builder.button(text='🔙 Назад', callback_data='start')

    builder.adjust(*[1] * len(channel_services), 1)

    await query.message.edit_text('<b>Управление каналами</b>\n'
                                  '\n'
                                  '⬇️ Загружено:\n'
                                  f'{loaded_text}'
                                  f'\n'
                                  f'<b>Выберите сервис для обновления каналов</b>', reply_markup=builder.as_markup())
