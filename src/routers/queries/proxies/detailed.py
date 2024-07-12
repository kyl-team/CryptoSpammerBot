import re

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from beanie import PydanticObjectId

from core.proxies import is_valid_proxy
from database import Proxy

detailed_router = Router()


@detailed_router.callback_query(F.data.regexp(re.compile(r'^proxies_([a-z0-9]+)(_([a-z]+))?$')))
async def detailed_proxy(query: CallbackQuery, match: re.Match[str]):
    proxy_id, action = match.group(1, 3)
    proxy = await Proxy.find_one(Proxy.id == PydanticObjectId(proxy_id))
    if not proxy:
        return await query.answer('❌ Прокси не найдено', show_alert=True)

    builder = InlineKeyboardBuilder()

    if action == 'delete':
        await proxy.delete()

        builder.button(text='🔙 Назад', callback_data='proxies')

        return await query.message.edit_text(f'✅ Прокси <code>{proxy.url}</code> удалено')
    elif action == 'check':
        if await is_valid_proxy(proxy.url):
            return await query.answer('✅ Соединение установлено')
        else:
            return await query.answer('❌ Не удалось установить соединение', show_alert=True)

    builder.button(text='🗑️ Удалить', callback_data=f'proxies_{proxy.id}_delete')
    builder.button(text='🔄️ Проверить соединение', callback_data=f'proxies_{proxy.id}_check')

    await query.message.edit_text(f'<b>Прокси <code>{proxy.url}</code></b>\n', reply_markup=builder.as_markup())
