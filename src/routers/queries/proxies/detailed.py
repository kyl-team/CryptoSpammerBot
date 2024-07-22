import re

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from beanie import PydanticObjectId

from database import Proxy

detailed_router = Router()


@detailed_router.callback_query(F.data.regexp(re.compile(r'^proxies_([a-f0-9]{24})(_([a-z]+))?$')).as_('match'))
async def detailed_proxy(query: CallbackQuery, match: re.Match[str]):
    proxy_id, action = match.group(1, 3)
    proxy = await Proxy.find_one(Proxy.id == PydanticObjectId(proxy_id))
    if not proxy:
        return await query.answer('❌ Прокси не найдено', show_alert=True)

    builder = InlineKeyboardBuilder()

    if action == 'delete':
        await proxy.delete()

        builder.button(text='🔙 Назад', callback_data='proxies')

        return await query.message.edit_text(f'✅ Прокси <code>{proxy}</code> удалено')
    elif action == 'check':
        if await proxy.check_connection():
            return await query.answer('✅ Соединение установлено')
        else:
            return await query.answer('❌ Не удалось установить соединение', show_alert=True)

    builder.button(text='🔄️ Проверить соединение', callback_data=f'proxies_{proxy.id}_check')
    builder.button(text='🗑️ Удалить', callback_data=f'proxies_{proxy.id}_delete')
    builder.button(text='🔙 Назад', callback_data=f'proxies')

    builder.adjust(2, 1)

    auth_text = f'Нужна авторизация: {"да" if proxy.require_auth else "нет"}\n'
    if proxy.require_auth:
        auth_text += f'Пользователь: <code>{proxy.username}</code>\n'
        auth_text += f'Пароль: <tg-spoiler>{proxy.password}</tg-spoiler>\n'

    await query.message.edit_text(f'<b>Прокси <code>{proxy.id}</code></b>\n'
                                  f'\n'
                                  f'Хост: <code>{proxy.hostname}</code>\n'
                                  f'Порт: <code>{proxy.port}</code>\n'
                                  f'\n'
                                  f'{auth_text}'
                                  f'\n'
                                  f'Строка подключения: <tg-spoiler><b>{proxy}</b></tg-spoiler>\n',
                                  reply_markup=builder.as_markup())
