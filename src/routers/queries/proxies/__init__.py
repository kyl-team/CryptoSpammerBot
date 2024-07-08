from aiogram import Router

from .add import add_router
from .menu import menu_router

proxies_router = Router()

proxies_router.include_routers(menu_router, add_router)
