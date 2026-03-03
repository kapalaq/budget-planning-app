"""Login and registration handlers for the Telegram bot."""

from aiogram import Router, types
from aiogram.fsm.context import FSMContext

from telegram.backend import _current_token, backend
from telegram.keyboards import auth_menu, cancel_keyboard
from telegram.states import Auth

router = Router()


@router.callback_query(lambda c: c.data == "auth:login")
async def cb_auth_login(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(Auth.login)
    await callback.message.edit_text(
        "Enter your login:", reply_markup=cancel_keyboard()
    )


@router.message(Auth.login)
async def process_login(message: types.Message, state: FSMContext):
    await state.update_data(login=message.text.strip())
    await state.set_state(Auth.password)
    await message.answer("Enter your password:", reply_markup=cancel_keyboard())


@router.message(Auth.password)
async def process_password(message: types.Message, state: FSMContext):
    data = await state.get_data()
    login = data["login"]
    password = message.text.strip()

    result = await backend.login(login, password, message.from_user.id)

    if result.get("status") == "error":
        await state.clear()
        await message.answer(
            f"Login failed: {result['message']}\n\nPlease try again.",
            reply_markup=auth_menu(),
        )
        return

    _current_token.set(result["token"])
    await state.clear()
    await message.answer(
        f"Logged in successfully! (user_id: {result['user_id']})\n"
        "Use /start to open the dashboard."
    )


@router.callback_query(lambda c: c.data == "auth:register")
async def cb_auth_register(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(Auth.register_login)
    await callback.message.edit_text(
        "Choose a login name:", reply_markup=cancel_keyboard()
    )


@router.message(Auth.register_login)
async def process_register_login(message: types.Message, state: FSMContext):
    await state.update_data(login=message.text.strip())
    await state.set_state(Auth.register_password)
    await message.answer("Choose a password:", reply_markup=cancel_keyboard())


@router.message(Auth.register_password)
async def process_register_password(message: types.Message, state: FSMContext):
    await state.update_data(password=message.text.strip())
    await state.set_state(Auth.register_confirm_password)
    await message.answer("Confirm your password:", reply_markup=cancel_keyboard())


@router.message(Auth.register_confirm_password)
async def process_register_confirm(message: types.Message, state: FSMContext):
    data = await state.get_data()
    password = data["password"]
    confirm = message.text.strip()

    if password != confirm:
        await state.clear()
        await message.answer(
            "Passwords do not match. Please try again.",
            reply_markup=auth_menu(),
        )
        return

    result = await backend.register(data["login"], password, message.from_user.id)

    if result.get("status") == "error":
        await state.clear()
        await message.answer(
            f"Registration failed: {result['message']}\n\nPlease try again.",
            reply_markup=auth_menu(),
        )
        return

    _current_token.set(result["token"])
    await state.clear()
    await message.answer(
        f"Registered successfully! (user_id: {result['user_id']})\n"
        "Use /start to open the dashboard."
    )
