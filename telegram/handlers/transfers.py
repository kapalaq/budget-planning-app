"""Transfer handler."""

from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from telegram.backend import backend
from telegram.keyboards import cancel_keyboard, back_to_menu, wallet_list_keyboard
from telegram.states import Transfer

router = Router()


@router.message(Command("transfer"))
async def cmd_transfer(message: types.Message, state: FSMContext):
    await _start_transfer(message, state)


@router.callback_query(F.data == "transfer")
async def cb_transfer(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await _start_transfer(callback.message, state)


async def _start_transfer(message: types.Message, state: FSMContext):
    await state.clear()
    resp = await backend.handle({"action": "get_transfer_context", "data": {}})
    if resp["status"] == "error":
        await message.answer(resp["message"], reply_markup=back_to_menu())
        return
    from_wallet = resp["data"]["from_wallet"]
    targets = resp["data"]["target_wallets"]
    if not targets:
        await message.answer(
            "No target wallets available.", reply_markup=back_to_menu()
        )
        return
    await state.update_data(from_wallet=from_wallet, targets=targets)
    await state.set_state(Transfer.target_wallet)
    await message.answer(
        f"Transfer from: {from_wallet['name']} "
        f"(balance: {from_wallet['balance']:.2f})\n"
        "Select target wallet:",
        reply_markup=wallet_list_keyboard(targets, action_prefix="xfer_to"),
    )


@router.callback_query(Transfer.target_wallet, F.data.startswith("xfer_to:"))
async def transfer_target(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    target_name = callback.data.split(":", 1)[1]
    await state.update_data(target_wallet_name=target_name)
    await state.set_state(Transfer.amount)
    await callback.message.answer(
        f"Target: {target_name}\nEnter amount:", reply_markup=cancel_keyboard()
    )


@router.message(Transfer.amount)
async def transfer_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        if amount <= 0:
            raise ValueError
    except (ValueError, AttributeError):
        await message.answer("Please enter a positive number.")
        return
    await state.update_data(amount=amount)
    await state.set_state(Transfer.description)
    await message.answer(
        "Enter description (or `-` to skip):", reply_markup=cancel_keyboard()
    )


@router.message(Transfer.description)
async def transfer_description(message: types.Message, state: FSMContext):
    desc = message.text.strip()
    if desc == "-":
        desc = ""
    await state.update_data(description=desc)
    await state.set_state(Transfer.date)
    await message.answer(
        "Enter date (YYYY-MM-DD) or `-` for today:", reply_markup=cancel_keyboard()
    )


@router.message(Transfer.date)
async def transfer_date(message: types.Message, state: FSMContext):
    text = message.text.strip()
    date_val = None if text == "-" else text
    data = await state.get_data()
    form = {
        "target_wallet_name": data["target_wallet_name"],
        "amount": data["amount"],
        "description": data.get("description", ""),
        "date": date_val,
    }
    resp = await backend.handle({"action": "transfer", "data": form})
    await state.clear()
    msg = resp.get("message", "Done")
    await message.answer(msg, reply_markup=back_to_menu())
