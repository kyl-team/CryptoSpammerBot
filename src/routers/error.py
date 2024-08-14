import traceback
from contextlib import suppress

from aiogram import Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import ErrorEvent, BufferedInputFile

from config import config
from core.job.worker.report import format_date

error_router = Router()


@error_router.error()
async def error_handler(e: ErrorEvent):
    stacktrace = '\n'.join(traceback.format_exception(e.exception))

    update_info = ''
    if e.update.callback_query:
        user = e.update.callback_query.from_user
        update_info = f'Пользователь: @{user.username} [{user.id}]. CallbackQuery'
        await e.update.callback_query.answer('❌ Что-то пошло не так', show_alert=True)
    elif e.update.message:
        user = e.update.message.from_user
        update_info = f'Пользователь: @{user.username} [{user.id}]. Message'
        await e.update.message.answer('❌ Что-то пошло не так')

    document = BufferedInputFile(stacktrace.encode(), 'Traceback.txt')

    timestamp = format_date()
    caption = f'Отчёт об ошибке от {timestamp}. {update_info}'

    for owner in config.telegram_bot.whitelist:
        with suppress(TelegramBadRequest):
            await e.update.bot.send_document(owner, document, caption=caption)
