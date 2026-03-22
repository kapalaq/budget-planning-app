"""Percentages handler."""

from aiogram import F, Router, types
from aiogram.filters import Command
from telegram.backend import backend, get_lang
from telegram.keyboards import back_to_menu, parse_menu_page
from telegram.utils import fmt_percentages

router = Router()


@router.message(Command("percentages"))
async def cmd_percentages(message: types.Message):
    await _show_percentages(message)


@router.callback_query(F.data.startswith("percentages"))
async def cb_percentages(callback: types.CallbackQuery):
    await callback.answer()
    page = parse_menu_page(callback.data, default=2)
    await _show_percentages(callback.message, menu_page=page)


async def _show_percentages(message: types.Message, menu_page: int = 2):
    resp = await backend.handle({"action": "get_percentages", "data": {}})
    if resp["status"] == "error":
        try:
            await message.edit_text(
                resp["message"], reply_markup=back_to_menu(menu_page)
            )
        except Exception:
            await message.answer(resp["message"], reply_markup=back_to_menu(menu_page))
        return
    text = fmt_percentages(resp["data"], lang=get_lang())
    try:
        await message.edit_text(
            text, parse_mode="MarkdownV2", reply_markup=back_to_menu(menu_page)
        )
    except Exception:
        await message.answer(
            text, parse_mode="MarkdownV2", reply_markup=back_to_menu(menu_page)
        )
