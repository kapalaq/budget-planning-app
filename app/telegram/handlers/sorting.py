"""Sorting handlers."""

from aiogram import F, Router, types
from languages import t
from telegram.backend import backend, get_lang
from telegram.keyboards import back_to_menu, parse_menu_page, sorting_keyboard

router = Router()


@router.callback_query(F.data.startswith("sorting"))
async def cb_sorting(callback: types.CallbackQuery):
    await callback.answer()
    page = parse_menu_page(callback.data, default=2)
    await _show_sorting(callback.message, menu_page=page)


async def _show_sorting(message: types.Message, menu_page: int = 2):
    resp = await backend.handle({"action": "get_sorting_options", "data": {}})
    options = resp["data"]["options"]
    await message.edit_text(
        "\U0001f522 " + t("sorting.tg_select", get_lang()),
        reply_markup=sorting_keyboard(options, menu_page=menu_page),
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


@router.callback_query(F.data.startswith("wallet_sorting"))
async def cb_wallet_sorting(callback: types.CallbackQuery):
    await callback.answer()
    page = parse_menu_page(callback.data, default=3)
    await _show_wallet_sorting(callback.message, menu_page=page)


async def _show_wallet_sorting(message: types.Message, menu_page: int = 3):
    resp = await backend.handle({"action": "get_wallet_sorting_options", "data": {}})
    options = resp["data"]["options"]
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    rows = [
        [InlineKeyboardButton(text=name, callback_data=f"wsort:{key}")]
        for key, name in options.items()
    ]
    rows.append(
        [InlineKeyboardButton(text="<< Menu", callback_data=f"menu_page:{menu_page}")]
    )
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    await message.edit_text(
        "\U0001f522 " + t("sorting.tg_wallet_select", get_lang()), reply_markup=kb
    )


@router.callback_query(F.data.startswith("wsort:"))
async def cb_set_wallet_sort(callback: types.CallbackQuery):
    await callback.answer()
    key = callback.data.split(":", 1)[1]
    resp = await backend.handle(
        {"action": "set_wallet_sorting", "data": {"strategy_key": key}}
    )
    msg = resp.get("message", "Done")
    await callback.message.edit_text(msg, reply_markup=back_to_menu(3))
