import re

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.sources import update_channels
from database import channel_services
from ..state_clear import get_state_clear_markup

update_router = Router()


class UpdateServiceStates(StatesGroup):
    php_session = State()


@update_router.callback_query(F.data.regexp(re.compile(r'sources_update_([a-z.]+)')).as_('match'))
async def update_source(query: CallbackQuery, match: re.Match[str], state: FSMContext):
    service = match.group(1)

    if service not in channel_services:
        return await query.answer('❌ Сервис не найден', show_alert=True)

    # if service == 'telemetr.me':
    #     await state.set_state(UpdateServiceStates.php_session)
    #     return await query.message.edit_text('<b>Введите PHPSESSID</b>', reply_markup=get_state_clear_markup())

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
