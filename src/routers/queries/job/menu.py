import re

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

menu_router = Router()


@menu_router.callback_query(F.data.regexp(re.compile(r'^job(_(\w+))?$')))
async def menu(query: CallbackQuery):
    builder = InlineKeyboardBuilder()

    builder.button(text='✏️ Редактировать сообщение', callback_data='job_edit')
    builder.button(text='🔙 Назад', callback_data='start')
    builder.button(text='Искать похожие ✅❌', callback_data='job_similar')

    builder.adjust(1, 2)

    await query.message.edit_text('<b>Создание задания</b>', reply_markup=builder.as_markup())
