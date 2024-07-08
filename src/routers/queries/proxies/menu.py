import math

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import Proxy

menu_router = Router()


@menu_router.callback_query(F.data == 'proxies')
async def proxies_menu(query: CallbackQuery):
    builder = InlineKeyboardBuilder()

    count = 0
    async for proxy in Proxy.find():
        builder.button(text=proxy.url, callback_data=f'proxies_{proxy.id}')
        count += 1

    builder.button(text='🔙 Назад', callback_data='start')
    builder.button(text='➕ Добавить', callback_data='proxies_add')

    builder.adjust(*[2] * math.floor(count / 2), *([1, 2] if count % 2 == 1 else [2]))

    await query.message.edit_text('<b>Управление прокси:</b>\n'
                                  '\n'
                                  f'Загружено: {count}', reply_markup=builder.as_markup())
