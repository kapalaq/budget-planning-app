"""Sorting handlers."""

from aiogram import Router, F, types

from telegram.backend import backend
from telegram.keyboards import sorting_keyboard, back_to_menu

router = Router()


@router.callback_query(F.data == "sorting")
async def cb_sorting(callback: types.CallbackQuery):
    await callback.answer()
    await _show_sorting(callback.message)


async def _show_sorting(message: types.Message):
    resp = await backend.handle({"action": "get_sorting_options", "data": {}})
    options = resp["data"]["options"]
    await message.edit_text(
        "\U0001f522 Select sorting method:", reply_markup=sorting_keyboard(options)
    )


@router.callback_query(F.data.startswith("sort:"))
async def cb_set_sort(callback: types.CallbackQuery):
    await callback.answer()
    key = callback.data.split(":", 1)[1]
    resp = await backend.handle(
        {"action": "set_sorting", "data": {"strategy_key": key}}
    )
    msg = resp.get("message", "Done")
    await callback.message.edit_text(msg, reply_markup=back_to_menu(2))


# ── Wallet sorting (page 3) ───────────────────────────────────────────────────


@router.callback_query(F.data == "wallet_sorting")
async def cb_wallet_sorting(callback: types.CallbackQuery):
    await callback.answer()
    await _show_wallet_sorting(callback.message)


async def _show_wallet_sorting(message: types.Message):
    resp = await backend.handle({"action": "get_wallet_sorting_options", "data": {}})
    options = resp["data"]["options"]
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    rows = [
        [InlineKeyboardButton(text=name, callback_data=f"wsort:{key}")]
        for key, name in options.items()
    ]
    rows.append([InlineKeyboardButton(text="<< Menu", callback_data="menu_page:3")])
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    await message.edit_text("\U0001f522 Select wallet sorting method:", reply_markup=kb)


@router.callback_query(F.data.startswith("wsort:"))
async def cb_set_wallet_sort(callback: types.CallbackQuery):
    await callback.answer()
    key = callback.data.split(":", 1)[1]
    resp = await backend.handle(
        {"action": "set_wallet_sorting", "data": {"strategy_key": key}}
    )
    msg = resp.get("message", "Done")
    await callback.message.edit_text(msg, reply_markup=back_to_menu(3))
