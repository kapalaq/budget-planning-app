"""Percentages handler."""

from aiogram import F, Router, types
from aiogram.filters import Command
from telegram.backend import backend, get_lang
from telegram.keyboards import back_to_menu
from telegram.utils import fmt_percentages

router = Router()


@router.message(Command("percentages"))
async def cmd_percentages(message: types.Message):
    await _show_percentages(message)


@router.callback_query(F.data == "percentages")
async def cb_percentages(callback: types.CallbackQuery):
    await callback.answer()
    await _show_percentages(callback.message)


async def _show_percentages(message: types.Message):
    resp = await backend.handle({"action": "get_percentages", "data": {}})
    if resp["status"] == "error":
        try:
            await message.edit_text(resp["message"], reply_markup=back_to_menu(2))
        except Exception:
            await message.answer(resp["message"], reply_markup=back_to_menu(2))
        return
    text = fmt_percentages(resp["data"], lang=get_lang())
    try:
        await message.edit_text(
            text, parse_mode="MarkdownV2", reply_markup=back_to_menu(2)
        )
    except Exception:
        await message.answer(
            text, parse_mode="MarkdownV2", reply_markup=back_to_menu(2)
        )
