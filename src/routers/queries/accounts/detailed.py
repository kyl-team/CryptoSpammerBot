import re

from aiogram import Router, F
from aiogram.types import CallbackQuery

from core.accounts import get_client
from database import Account

detailed_router = Router()


@detailed_router.callback_query(F.data.regexp(re.compile(r'^accounts_(\d+)$')).as_('match'))
async def get_detailed_account(query: CallbackQuery, match: re.Match[str]):
    user_id = int(match.group(1))
    account = await Account.find_one(Account.user_id == user_id)
    if not account:
        return await query.answer('❌ Аккаунт не найден', show_alert=True)

    client = get_client(account.phone, session_string=account.session)
    if not client.is_connected:
        await client.connect()

    async for dialog in client.get_dialogs():
        print(dialog.chat.username)

    await query.message.edit_text(f'<b>Аккаунт @{account.username} [<code>{account.user_id}</code>]</b>\n'
                                  f'\n'
                                  f'Чатов: ')
