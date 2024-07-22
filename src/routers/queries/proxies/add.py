import re

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import Proxy
from database.proxy import proxy_pattern
from routers.queries.state_clear import get_state_clear_markup

add_router = Router()


class AddProxy(StatesGroup):
    url = State()


@add_router.callback_query(F.data == 'proxies_add')
async def add_proxy(query: CallbackQuery, state: FSMContext):
    await state.set_state(AddProxy.url)
    await query.message.edit_text('<b>Введите URL HTTP прокси</b>', reply_markup=get_state_clear_markup())


@add_router.message(StateFilter(AddProxy.url), F.text.regexp(proxy_pattern).as_('match'))
async def on_url_proxy(message: Message, match: re.Match[str]):
    status_message = await message.reply('⌛ Проверка соединения')

    proxy = Proxy.from_match(match)

    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 В главное меню', callback_data='start')
    builder.button(text='🔙 В управление проксями', callback_data='proxies')
    builder.adjust(2)

    if await proxy.check_connection():
        await proxy.insert()

        await status_message.edit_text('✅ Прокси добавлено. Соединение подтверждено', reply_markup=builder.as_markup())
    else:
        await status_message.edit_text(
            '❌ Не удалось установить соединение с прокси.\n'
            'Возможно вы указали неверные авторизационные данные', reply_markup=builder.as_markup())
