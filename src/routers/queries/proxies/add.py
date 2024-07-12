import re

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.proxies import is_valid_proxy
from database import Proxy
from routers.queries.state_clear import get_state_clear_markup

add_router = Router()


class AddProxy(StatesGroup):
    url = State()


@add_router.callback_query(F.data == 'proxies_add')
async def add_proxy(query: CallbackQuery, state: FSMContext):
    await state.set_state(AddProxy.url)
    await query.message.edit_text('<b>Введите URL HTTP прокси</b>', reply_markup=get_state_clear_markup())


proxy_url_pattern = re.compile(r'^(http://)?((\w+:\w+@)?\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5})$')


@add_router.message(StateFilter(AddProxy.url), F.text.regexp(proxy_url_pattern).as_('match'))
async def on_url_proxy(message: Message, match: re.Match[str]):
    status_message = await message.reply('⌛ Проверка соединения')

    proxy_url = match.group(2)

    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 В главное меню', callback_data='start')
    builder.button(text='🔙 В управление проксями', callback_data='proxies')
    builder.adjust(2)

    if await is_valid_proxy(proxy_url):
        proxy = Proxy(url=proxy_url)
        await proxy.insert()

        await status_message.edit_text('✅ Прокси добавлено. Соединение подтверждено', reply_markup=builder.as_markup())
    else:
        await status_message.edit_text(
            '❌ Не удалось установить соединение с прокси.\n'
            'Возможно вы указали неверные авторизационные данные', reply_markup=builder.as_markup())
