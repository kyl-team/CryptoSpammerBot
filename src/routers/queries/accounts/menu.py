import math

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import Account

menu_router = Router()


@menu_router.callback_query(F.data == 'accounts')
async def menu(query: CallbackQuery):
    builder = InlineKeyboardBuilder()

    count = 0
    async for account in Account.find():
        builder.button(text=account.id, callback_data=f'accounts_{account.id}')
        count += 1

    builder.button(text='🔙 Назад', callback_data='start')
    builder.button(text='➕ Добавить', callback_data='accounts_add')

    builder.adjust(*[2] * math.floor(count / 2), *([1, 2] if count % 2 == 1 else [2]))

    await query.message.edit_text('<b>Управление аккаунтами:</b>\n'
                                  '\n'
                                  f'Загружено: {count}', reply_markup=builder.as_markup())
