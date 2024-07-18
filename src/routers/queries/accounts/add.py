import re

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from pyrofork.errors import SessionPasswordNeeded, PhoneCodeExpired

from core.accounts import get_client
from database import Account
from ..state_clear import get_state_clear_markup


def get_back_markup():
    builder = InlineKeyboardBuilder()

    builder.button(text='🔙 Назад', callback_data='accounts')
    return builder.as_markup()


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
    password = State()


@add_router.callback_query(F.data == 'accounts_add_manual')
async def add_account_manual(query: CallbackQuery, state: FSMContext):
    await state.set_state(ManualAddGroup.phone)
    await query.message.edit_text('<b>Введите номер телефона</b>')


@add_router.message(StateFilter(ManualAddGroup.phone), F.text.regexp(re.compile('^[0-9]{11,}$')))
async def enter_phone(message: Message, state: FSMContext):
    phone = message.text

    if await Account.find_one(Account.phone == phone):
        return await message.reply('❌ Аккаунт с этим номером уже добавлен', reply_markup=get_back_markup())

    client = get_client(phone)
    if client.is_connected:
        raise RuntimeError('Illegal client connection')

    await client.connect()
    sent_code = await client.send_code(phone)
    await state.set_state(ManualAddGroup.code)
    await state.set_data({'phone': phone, 'phone_hash': sent_code.phone_code_hash})
    await message.reply('<b>Введите код (SMS или пуш)</b>\n'
                        '\n'
                        'Телеграм заблокирует вход в Ваш аккаунт, если вы перешлете код боту. '
                        'Если вы хотите добавить себя, добавьте "-" между цифрами кода, чтобы телеграм '
                        'не распознал его и дал Вам войти. Например: 35135 -> 3-51-3-5',
                        reply_markup=get_state_clear_markup())


@add_router.message(ManualAddGroup.code, F.text)
@add_router.message(ManualAddGroup.password, F.text)
async def enter_code_or_password(message: Message, state: FSMContext):
    current_state = await state.get_state()
    data = await state.get_data()
    phone, phone_hash = data['phone'], data['phone_hash']
    client = get_client(phone)

    if current_state == ManualAddGroup.code:
        code = message.text

        try:
            await client.sign_in(phone, phone_hash, code)
            await client.prof
        except SessionPasswordNeeded:
            await state.set_state(ManualAddGroup.password)
            return await message.reply('⚠️ Введите пароль 2FA аутентификации', reply_markup=get_state_clear_markup())
        except PhoneCodeExpired:
            await state.clear()
            return await message.reply('❌ Код устарел', reply_markup=get_back_markup())
    elif current_state == ManualAddGroup.password:
        password = message.text
        await client.check_password(password)
    else:
        raise RuntimeError('Not possible state')

    await state.clear()

    me = await client.get_me()

    account = Account(phone=phone, session=await client.export_session_string(), username=me.username, user_id=me.id)
    await account.insert()

    await message.reply(f'✅ Вход в аккаунт @{me.username} успешен [{me.id}]', reply_markup=get_back_markup())
