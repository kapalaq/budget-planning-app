"""Percentages handler."""

from aiogram import Router, F, types
from aiogram.filters import Command

from telegram.backend import backend
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
        await message.answer(resp["message"], reply_markup=back_to_menu())
        return
    text = fmt_percentages(resp["data"])
    await message.answer(text, parse_mode="MarkdownV2", reply_markup=back_to_menu())
