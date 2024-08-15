from aiogram import Router

from .menu import menu_router
from .stop import stop_router

job_router = Router()

job_router.include_routers(menu_router, stop_router)
