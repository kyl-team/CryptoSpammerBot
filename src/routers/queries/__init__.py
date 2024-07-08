from aiogram import Router

from .accounts import accounts_router
from .job import job_router
from .proxies import proxies_router
from .sources import sources_router
from .state_clear import state_clear_router

queries_router = Router()

queries_router.include_routers(accounts_router, job_router, sources_router, proxies_router, state_clear_router)
