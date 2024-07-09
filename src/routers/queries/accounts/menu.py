from aiogram import Router, F
from aiogram.types import CallbackQuery

menu_router = Router()


@menu_router.callback_query(F.data == 'accounts')
async def menu(query: CallbackQuery):
    pass
