"""Disconnect handler for the Telegram bot."""

from aiogram import Router, types
from aiogram.fsm.context import FSMContext

from telegram.backend import backend
from telegram.keyboards import confirm_keyboard

router = Router()


@router.callback_query(lambda c: c.data == "disconnect")
async def cb_disconnect(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text(
        "\U0001f6aa Are you sure you want to disconnect your Telegram account?",
        reply_markup=confirm_keyboard("disconnect"),
    )


@router.callback_query(lambda c: c.data == "confirm_disconnect:")
async def cb_confirm_disconnect(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    tg_id = callback.from_user.id
    await backend.disconnect(tg_id)
    await callback.message.edit_text(
        "\u2705 Telegram account disconnected.\n\n"
        "To reconnect, generate a new link from the CLI app and use /start."
    )
