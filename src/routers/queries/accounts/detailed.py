import re

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.accounts import get_client
from database import Account

detailed_router = Router()


@detailed_router.callback_query(F.data.regexp(re.compile(r'^accounts_(\d+)(_(delete))?$')).as_('match'))
async def get_detailed_account(query: CallbackQuery, match: re.Match[str]):
    user_id, action = match.group(1, 3)
    account = await Account.find_one(Account.user_id == int(user_id))
    if not account:
        return await query.answer('❌ Аккаунт не найден', show_alert=True)

    builder = InlineKeyboardBuilder()
    builder.button(text='🗑️ Удалить', callback_data=f'accounts_{account.user_id}_delete')
    builder.button(text='🔙 Назад', callback_data='accounts')
    builder.adjust(1, 1)

    if action == 'delete':
        await account.delete()
        builder = InlineKeyboardBuilder()
        builder.button(text='🔙 Назад', callback_data='accounts')
        return await query.message.edit_text('✅ Аккаунт удален', reply_markup=builder.as_markup())

    client = get_client(account.phone, session_string=account.session)
    if not client.is_connected:
        await client.connect()

    await query.message.edit_text(f'<b>Аккаунт @{account.username} [<code>{account.user_id}</code>]</b>\n'
                                  f'\n'
                                  f'Телефон: <code>{account.phone}</code>', reply_markup=builder.as_markup())
