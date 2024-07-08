from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import config

bot = Bot(config.telegram_bot.token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

dp.message.filter(
    F.from_user.id.in_(config.telegram_bot.whitelist)
)

dp.callback_query.filter(
    F.from_user.id.in_(config.telegram_bot.whitelist)
)


async def start():
    await dp.start_polling(bot)
