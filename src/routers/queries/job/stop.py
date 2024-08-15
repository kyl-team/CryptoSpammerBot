import re

from aiogram import Router, F
from aiogram.types import CallbackQuery

from core.job.worker import online

stop_router = Router()


@stop_router.callback_query(F.regexp(re.compile(r'^job_stop_[a-z0-9]{8}$')).as_('match'))
async def stop_task(query: CallbackQuery, match: re.Match[str]):
    state_id = match.group(1)

    online.states[state_id].stop()

    await query.answer('✅ Остановка запрошена', show_alert=True)
