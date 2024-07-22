from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import Proxy, Channel, Account

start_router = Router()


@start_router.message(CommandStart())
@start_router.callback_query(F.data == 'start')
async def start_command(event: Message | CallbackQuery):
    builder = InlineKeyboardBuilder()

    builder.button(text='🥇 Источники каналов', callback_data='sources')
    builder.button(text='🌐 Прокси', callback_data='proxies')
    builder.button(text='👥 Аккаунты', callback_data='accounts')
    builder.button(text='⛏️ К работе', callback_data='job')

    builder.adjust(1, 2, 1)

    channels_count = await Channel.count()
    proxies_count = await Proxy.count()
    accounts_count = await Account.count()

    kwargs = {
        'text': (
            '<b>Добро пожаловать в бота!</b>\n'
            '\n'
            f'Каналов загружено: <code>{channels_count}</code>\n'
            f'Прокси загружено: <code>{proxies_count}</code>\n'
            f'Аккаунтов загружено: <code>{accounts_count}</code>'
        ),
        'reply_markup': builder.as_markup()
    }

    if isinstance(event, Message):
        await event.reply(**kwargs)
    elif isinstance(event, CallbackQuery):
        await event.message.edit_text(**kwargs)
