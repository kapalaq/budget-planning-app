"""Common handlers: cancel, text-based commands."""

from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from telegram.backend import backend
from telegram.keyboards import back_to_menu
from telegram.utils import fmt_transaction

router = Router()


@router.callback_query(F.data == "cancel")
async def cb_cancel(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("Cancelled")
    await state.clear()
    await callback.message.answer("Cancelled.", reply_markup=back_to_menu())


# ── Text-based indexed commands: show N, edit N, delete N ────────────


@router.message(lambda m: m.text and m.text.strip().lower().startswith("show "))
async def text_show(message: types.Message):
    parts = message.text.strip().split()
    if len(parts) != 2:
        return
    try:
        index = int(parts[1])
    except ValueError:
        return
    resp = await backend.handle({"action": "get_transaction", "data": {"index": index}})
    if resp["status"] == "error":
        await message.answer(resp["message"], reply_markup=back_to_menu())
        return
    text = fmt_transaction(resp["data"])
    from telegram.keyboards import transaction_actions_keyboard

    await message.answer(
        text,
        parse_mode="MarkdownV2",
        reply_markup=transaction_actions_keyboard(index),
    )


@router.message(lambda m: m.text and m.text.strip().lower().startswith("wallet "))
async def text_wallet(message: types.Message):
    name = message.text.strip().split(maxsplit=1)[1]
    resp = await backend.handle({"action": "get_wallet_detail", "data": {"name": name}})
    if resp["status"] == "error":
        await message.answer(resp["message"], reply_markup=back_to_menu())
        return
    from telegram.utils import fmt_wallet_detail
    from telegram.keyboards import wallet_actions_keyboard

    text = fmt_wallet_detail(resp["data"])
    await message.answer(
        text, parse_mode="MarkdownV2", reply_markup=wallet_actions_keyboard(name)
    )


@router.message(lambda m: m.text and m.text.strip().lower().startswith("switch "))
async def text_switch(message: types.Message):
    name = message.text.strip().split(maxsplit=1)[1]
    resp = await backend.handle({"action": "switch_wallet", "data": {"name": name}})
    msg = resp.get("message", "Done")
    await message.answer(msg, reply_markup=back_to_menu())
