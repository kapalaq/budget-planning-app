"""Wallet handlers."""

from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from telegram.backend import backend
from telegram.keyboards import (
    back_to_menu,
    cancel_keyboard,
    wallet_type_keyboard,
    wallet_list_keyboard,
    wallet_actions_keyboard,
    edit_wallet_fields_keyboard,
    confirm_keyboard,
    capitalization_keyboard,
)
from telegram.states import AddWallet, EditWallet
from telegram.utils import fmt_wallets, fmt_wallet_detail

router = Router()


# ── List wallets ─────────────────────────────────────────────────────


@router.message(Command("wallets"))
async def cmd_wallets(message: types.Message):
    await _show_wallets(message)


@router.callback_query(F.data == "wallets")
async def cb_wallets(callback: types.CallbackQuery):
    await callback.answer()
    await _show_wallets(callback.message)


async def _show_wallets(message: types.Message):
    resp = await backend.handle({"action": "get_wallets", "data": {}})
    if resp["status"] == "error":
        await message.answer(resp["message"], reply_markup=back_to_menu())
        return
    text = fmt_wallets(resp["data"])
    wallets = resp["data"]["wallets"]
    await message.answer(
        text,
        parse_mode="MarkdownV2",
        reply_markup=wallet_list_keyboard(wallets, action_prefix="wdet"),
    )


# ── Wallet detail ────────────────────────────────────────────────────


@router.callback_query(F.data.startswith("wdet:"))
async def cb_wallet_detail(callback: types.CallbackQuery):
    await callback.answer()
    name = callback.data.split(":", 1)[1]
    resp = await backend.handle({"action": "get_wallet_detail", "data": {"name": name}})
    if resp["status"] == "error":
        await callback.message.answer(resp["message"], reply_markup=back_to_menu())
        return
    text = fmt_wallet_detail(resp["data"])
    await callback.message.answer(
        text, parse_mode="MarkdownV2", reply_markup=wallet_actions_keyboard(name)
    )


# ── Switch wallet ────────────────────────────────────────────────────


@router.callback_query(F.data.startswith("sw:"))
async def cb_switch_wallet(callback: types.CallbackQuery):
    await callback.answer()
    name = callback.data.split(":", 1)[1]
    resp = await backend.handle({"action": "switch_wallet", "data": {"name": name}})
    msg = resp.get("message", "Done")
    await callback.message.answer(msg, reply_markup=back_to_menu())


@router.message(Command("switch"))
async def cmd_switch(message: types.Message):
    parts = message.text.strip().split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Usage: /switch <wallet_name>")
        return
    name = parts[1]
    resp = await backend.handle({"action": "switch_wallet", "data": {"name": name}})
    msg = resp.get("message", "Done")
    await message.answer(msg, reply_markup=back_to_menu())


# ── Add wallet ───────────────────────────────────────────────────────


@router.message(Command("add_wallet"))
async def cmd_add_wallet(message: types.Message, state: FSMContext):
    await _start_add_wallet(message, state)


@router.callback_query(F.data == "add_wallet")
async def cb_add_wallet(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await _start_add_wallet(callback.message, state)


async def _start_add_wallet(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(AddWallet.wallet_type)
    await message.answer("Select wallet type:", reply_markup=wallet_type_keyboard())


@router.callback_query(AddWallet.wallet_type, F.data.startswith("wtype:"))
async def add_wallet_type(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    wtype = callback.data.split(":", 1)[1]
    await state.update_data(wallet_type=wtype)
    await state.set_state(AddWallet.name)
    await callback.message.answer("Enter wallet name:", reply_markup=cancel_keyboard())


@router.message(AddWallet.name)
async def add_wallet_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    if not name:
        await message.answer("Name cannot be empty.")
        return
    await state.update_data(name=name)
    await state.set_state(AddWallet.currency)
    await message.answer(
        "Enter currency (or `-` for KZT):", reply_markup=cancel_keyboard()
    )


@router.message(AddWallet.currency)
async def add_wallet_currency(message: types.Message, state: FSMContext):
    text = message.text.strip()
    currency = "KZT" if text == "-" else text.upper()
    await state.update_data(currency=currency)
    await state.set_state(AddWallet.starting_value)
    await message.answer(
        "Enter starting balance (or `-` for 0):", reply_markup=cancel_keyboard()
    )


@router.message(AddWallet.starting_value)
async def add_wallet_starting(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if text == "-":
        value = 0.0
    else:
        try:
            value = float(text)
        except ValueError:
            await message.answer("Please enter a valid number.")
            return
    await state.update_data(starting_value=value)
    await state.set_state(AddWallet.description)
    await message.answer(
        "Enter description (or `-` to skip):", reply_markup=cancel_keyboard()
    )


@router.message(AddWallet.description)
async def add_wallet_description(message: types.Message, state: FSMContext):
    desc = message.text.strip()
    if desc == "-":
        desc = ""
    await state.update_data(description=desc)
    data = await state.get_data()
    if data["wallet_type"] == "deposit":
        await state.set_state(AddWallet.interest_rate)
        await message.answer(
            "Enter interest rate (% per year):", reply_markup=cancel_keyboard()
        )
    else:
        await _finish_add_wallet(message, state)


@router.message(AddWallet.interest_rate)
async def add_wallet_rate(message: types.Message, state: FSMContext):
    try:
        rate = float(message.text.strip())
        if rate <= 0:
            raise ValueError
    except (ValueError, AttributeError):
        await message.answer("Please enter a positive number.")
        return
    await state.update_data(interest_rate=rate)
    await state.set_state(AddWallet.term_months)
    await message.answer("Enter term in months:", reply_markup=cancel_keyboard())


@router.message(AddWallet.term_months)
async def add_wallet_term(message: types.Message, state: FSMContext):
    try:
        term = int(message.text.strip())
        if term <= 0:
            raise ValueError
    except (ValueError, AttributeError):
        await message.answer("Please enter a positive integer.")
        return
    await state.update_data(term_months=term)
    await state.set_state(AddWallet.capitalization)
    await message.answer("Capitalization?", reply_markup=capitalization_keyboard())


@router.callback_query(AddWallet.capitalization, F.data.startswith("cap:"))
async def add_wallet_cap(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    cap = callback.data.split(":")[1] == "yes"
    await state.update_data(capitalization=cap)
    await _finish_add_wallet(callback.message, state)


async def _finish_add_wallet(message: types.Message, state: FSMContext):
    data = await state.get_data()
    form = {
        "wallet_type": data["wallet_type"],
        "name": data["name"],
        "currency": data["currency"],
        "starting_value": data["starting_value"],
        "description": data.get("description", ""),
    }
    if data["wallet_type"] == "deposit":
        form["interest_rate"] = data["interest_rate"]
        form["term_months"] = data["term_months"]
        form["capitalization"] = data["capitalization"]
    resp = await backend.handle({"action": "add_wallet", "data": form})
    await state.clear()
    msg = resp.get("message", "Done")
    await message.answer(msg, reply_markup=back_to_menu())


# ── Edit wallet ──────────────────────────────────────────────────────


@router.callback_query(F.data.startswith("edit_w:"))
async def cb_edit_wallet(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    name = callback.data.split(":", 1)[1]
    resp = await backend.handle({"action": "get_wallet_detail", "data": {"name": name}})
    if resp["status"] == "error":
        await callback.message.answer(resp["message"], reply_markup=back_to_menu())
        return
    await state.clear()
    await state.update_data(edit_wallet_name=name, edit_data={}, current=resp["data"])
    await state.set_state(EditWallet.field_select)
    await callback.message.answer(
        f"Editing wallet '{name}'. Select field:",
        reply_markup=edit_wallet_fields_keyboard(name),
    )


@router.callback_query(EditWallet.field_select, F.data.startswith("ewf:"))
async def cb_edit_wallet_field(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    parts = callback.data.split(":")
    name = parts[1]
    field = parts[2]
    data = await state.get_data()

    if field == "save":
        edit_data = data.get("edit_data", {})
        if not edit_data:
            await callback.message.answer(
                "No changes made.", reply_markup=back_to_menu()
            )
            await state.clear()
            return
        edit_data["name"] = name
        resp = await backend.handle({"action": "edit_wallet", "data": edit_data})
        await state.clear()
        msg = resp.get("message", "Done")
        await callback.message.answer(msg, reply_markup=back_to_menu())
        return

    if field == "name":
        await state.set_state(EditWallet.new_name)
        await callback.message.answer(
            "Enter new wallet name:", reply_markup=cancel_keyboard()
        )
    elif field == "currency":
        await state.set_state(EditWallet.currency)
        await callback.message.answer(
            "Enter new currency:", reply_markup=cancel_keyboard()
        )
    elif field == "description":
        await state.set_state(EditWallet.description)
        await callback.message.answer(
            "Enter new description (or `-` to clear):",
            reply_markup=cancel_keyboard(),
        )


@router.message(EditWallet.new_name)
async def edit_wallet_name(message: types.Message, state: FSMContext):
    new_name = message.text.strip()
    if not new_name:
        await message.answer("Name cannot be empty.")
        return
    data = await state.get_data()
    edit_data = data.get("edit_data", {})
    edit_data["new_name"] = new_name
    name = data["edit_wallet_name"]
    await state.update_data(edit_data=edit_data)
    await state.set_state(EditWallet.field_select)
    await message.answer(
        f"Name will be changed to '{new_name}'. Select another field or Save:",
        reply_markup=edit_wallet_fields_keyboard(name),
    )


@router.message(EditWallet.currency)
async def edit_wallet_currency(message: types.Message, state: FSMContext):
    currency = message.text.strip().upper()
    data = await state.get_data()
    edit_data = data.get("edit_data", {})
    edit_data["currency"] = currency
    name = data["edit_wallet_name"]
    await state.update_data(edit_data=edit_data)
    await state.set_state(EditWallet.field_select)
    await message.answer(
        f"Currency will be changed to '{currency}'. Select another field or Save:",
        reply_markup=edit_wallet_fields_keyboard(name),
    )


@router.message(EditWallet.description)
async def edit_wallet_desc(message: types.Message, state: FSMContext):
    desc = message.text.strip()
    if desc == "-":
        desc = ""
    data = await state.get_data()
    edit_data = data.get("edit_data", {})
    edit_data["description"] = desc
    name = data["edit_wallet_name"]
    await state.update_data(edit_data=edit_data)
    await state.set_state(EditWallet.field_select)
    await message.answer(
        "Description updated. Select another field or Save:",
        reply_markup=edit_wallet_fields_keyboard(name),
    )


# ── Delete wallet ────────────────────────────────────────────────────


@router.callback_query(F.data.startswith("del_w:"))
async def cb_delete_wallet(callback: types.CallbackQuery):
    await callback.answer()
    name = callback.data.split(":", 1)[1]
    await callback.message.answer(
        f"Delete wallet '{name}'?",
        reply_markup=confirm_keyboard("delw", name),
    )


@router.callback_query(F.data.startswith("confirm_delw:"))
async def cb_confirm_delete_wallet(callback: types.CallbackQuery):
    await callback.answer()
    name = callback.data.split(":")[1]
    resp = await backend.handle({"action": "delete_wallet", "data": {"name": name}})
    msg = resp.get("message", "Done")
    await callback.message.answer(msg, reply_markup=back_to_menu())
