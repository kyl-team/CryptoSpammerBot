from aiogram import Router

from .menu import menu_router

job_router = Router()

job_router.include_routers(menu_router)
