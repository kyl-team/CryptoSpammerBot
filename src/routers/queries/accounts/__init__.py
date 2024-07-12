from aiogram import Router

from .menu import menu_router
from .add import add_router

accounts_router = Router()

accounts_router.include_routers(menu_router, add_router)
