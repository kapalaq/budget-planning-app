"""Dashboard and start handlers."""

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from telegram.backend import backend
from telegram.keyboards import main_menu, back_to_menu
from telegram.utils import fmt_dashboard, _to_md2

router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await _send_dashboard(message)


@router.message(Command("dashboard", "home", "menu"))
async def cmd_dashboard(message: types.Message, state: FSMContext):
    await state.clear()
    await _send_dashboard(message)


@router.callback_query(lambda c: c.data == "dashboard")
async def cb_dashboard(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    resp = await backend.handle({"action": "process_recurring", "data": {}})
    count = resp.get("data", {}).get("generated_count", 0)

    resp = await backend.handle({"action": "get_dashboard", "data": {}})
    if resp["status"] == "error":
        await callback.message.edit_text(resp["message"], reply_markup=back_to_menu())
        return

    text = fmt_dashboard(resp["data"])
    if count > 0:
        prefix = _to_md2(f"{count} recurring transaction(s) generated")
        text = f"{prefix}\n\n{text}"

    try:
        await callback.message.edit_text(
            text, reply_markup=main_menu(), parse_mode="MarkdownV2"
        )
    except Exception:
        await callback.message.answer(
            text, reply_markup=main_menu(), parse_mode="MarkdownV2"
        )


async def _send_dashboard(message: types.Message):
    await backend.handle({"action": "process_recurring", "data": {}})
    resp = await backend.handle({"action": "get_dashboard", "data": {}})
    if resp["status"] == "error":
        await message.answer(resp["message"])
        return
    text = fmt_dashboard(resp["data"])
    await message.answer(text, reply_markup=main_menu(), parse_mode="MarkdownV2")
