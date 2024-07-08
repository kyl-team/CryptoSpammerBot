from aiogram import Router

from .menu import menu_router
from .update import update_router

sources_router = Router()

sources_router.include_routers(menu_router, update_router)
