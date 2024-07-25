import re

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core import job
from ..state_clear import get_state_clear_markup


class JobMessageStates(StatesGroup):
    edit = State()


menu_router = Router()


@menu_router.callback_query(F.data.regexp(re.compile(r'^job(_([a-z]+))?$')).as_('match'))
async def menu(query: CallbackQuery, state: FSMContext, match: re.Match[str]):
    action = match.group(2)

    match action:
        case 'similar':
            job.storage.similar = not job.storage.similar
            await job.storage.save()
        case 'edit':
            await state.set_state(JobMessageStates.edit)
            return await query.message.edit_text('<b>Введите сообщение для отправки владельцам бесед</b>',
                                                 reply_markup=get_state_clear_markup())
        case 'start':
            await job.start(query.from_user.id)
            return await query.message.edit_text('⌛ <b>Запуск работы...</b>')

    builder = InlineKeyboardBuilder()

    builder.button(text='✏️ Редактировать сообщение', callback_data='job_edit')
    if job.storage.similar:
        builder.button(text='Искать похожие ✅', callback_data='job_similar')
    else:
        builder.button(text='Искать похожие ❌', callback_data='job_similar')
    builder.button(text='🔙 Назад', callback_data='start')
    builder.button(text='🚀 Запуск', callback_data='job_start')

    builder.adjust(1, 1, 2)

    await query.message.edit_text('<b>Создание задания</b>', reply_markup=builder.as_markup())


@menu_router.message(StateFilter(JobMessageStates.edit), F.text)
async def edit_message(message: Message):
    job.storage.message.text = message.text
    await job.storage.save()

    builder = InlineKeyboardBuilder()

    builder.button(text='🔙 К параметрам запуска', callback_data='job')
    builder.button(text='🔙 В главное меню', callback_data='start')

    builder.adjust(1, 1)

    await message.reply('✅ Сообщение успешно установлено', reply_markup=builder.as_markup())
