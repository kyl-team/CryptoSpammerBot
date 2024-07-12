from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

add_router = Router()


@add_router.callback_query(F.data == 'accounts_add')
async def add_account(query: CallbackQuery):
    builder = InlineKeyboardBuilder()

    builder.button(text='🤖 Смс активаторы', callback_data='accounts_add_auto')
    builder.button(text='🔨 Вручную', callback_data='accounts_add_manual')
    builder.button(text='🔙 Назад', callback_data='accounts')

    builder.adjust(2, 1)

    await query.message.edit_text('<b>Выберите способ добавления сессий</b>', reply_markup=builder.as_markup())


class ManualAddGroup(StatesGroup):
    phone = State()
    code = State()


@add_router.callback_query(F.data == 'accounts_add_manual')
async def add_account_manual(query: CallbackQuery, state: FSMContext):
    pass
