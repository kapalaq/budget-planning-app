"""Wallet handlers."""

from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from languages import t
from telegram.backend import backend, get_lang
from telegram.keyboards import (
    back_to_menu,
    cancel_keyboard,
    skip_keyboard,
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


# ── Wallet list pickers (from paginated menu) ────────────────────────


async def _fetch_wallets():
    resp = await backend.handle({"action": "get_wallets", "data": {}})
    if resp["status"] == "error":
        return None, resp["message"]
    return resp["data"]["wallets"], None


@router.callback_query(F.data == "wallet_list_show")
async def cb_wallet_list_show(callback: types.CallbackQuery):
    await callback.answer()
    wallets, err = await _fetch_wallets()
    if err:
        await callback.message.edit_text(err, reply_markup=back_to_menu(3))
        return
    await callback.message.edit_text(
        "\U0001f4cb " + t("wallet.tg_select_to_view", get_lang()),
        reply_markup=wallet_list_keyboard(wallets, action_prefix="wdet"),
    )


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
        await message.edit_text(resp["message"], reply_markup=back_to_menu(3))
        return
    text = fmt_wallets(resp["data"], lang=get_lang())
    wallets = resp["data"]["wallets"]
    await message.edit_text(
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
        await callback.message.edit_text(resp["message"], reply_markup=back_to_menu(3))
        return
    text = fmt_wallet_detail(resp["data"], lang=get_lang())
    await callback.message.edit_text(
        text, parse_mode="MarkdownV2", reply_markup=wallet_actions_keyboard(name)
    )


# ── Switch wallet ────────────────────────────────────────────────────


@router.callback_query(F.data.startswith("sw:"))
async def cb_switch_wallet(callback: types.CallbackQuery):
    await callback.answer()
    name = callback.data.split(":", 1)[1]
    resp = await backend.handle({"action": "switch_wallet", "data": {"name": name}})
    msg = resp.get("message", "Done")
    await callback.message.edit_text(msg, reply_markup=back_to_menu(3))


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
    await message.edit_text(
        "\U0001f45b " + t("wallet.tg_select_type", get_lang()),
        reply_markup=wallet_type_keyboard(),
    )


@router.callback_query(AddWallet.wallet_type, F.data.startswith("wtype:"))
async def add_wallet_type(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    wtype = callback.data.split(":", 1)[1]
    await state.update_data(wallet_type=wtype)
    await state.set_state(AddWallet.name)
    await callback.message.edit_text(
        "\u270f\ufe0f " + t("wallet.tg_enter_name", get_lang()),
        reply_markup=cancel_keyboard(3),
    )


@router.message(AddWallet.name)
async def add_wallet_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    if not name:
        await message.answer("\u26a0\ufe0f " + t("wallet.tg_name_empty", get_lang()))
        return
    await state.update_data(name=name)
    await state.set_state(AddWallet.currency)
    await message.answer(
        "\U0001f4b1 " + t("wallet.tg_enter_currency", get_lang()),
        reply_markup=skip_keyboard(3),
    )


@router.callback_query(AddWallet.currency, F.data == "skip_default")
async def add_wallet_skip_currency(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(currency="KZT")
    await state.set_state(AddWallet.starting_value)
    await callback.message.edit_text(
        "\U0001f4b2 " + t("wallet.tg_enter_starting", get_lang()),
        reply_markup=skip_keyboard(3),
    )


@router.message(AddWallet.currency)
async def add_wallet_currency(message: types.Message, state: FSMContext):
    text = message.text.strip()
    currency = "KZT" if text == "-" or text.lower() == "skip" else text.upper()
    await state.update_data(currency=currency)
    await state.set_state(AddWallet.starting_value)
    await message.answer(
        "\U0001f4b2 " + t("wallet.tg_enter_starting", get_lang()),
        reply_markup=skip_keyboard(3),
    )


@router.callback_query(AddWallet.starting_value, F.data == "skip_default")
async def add_wallet_skip_starting(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(starting_value=0.0)
    await state.set_state(AddWallet.description)
    await callback.message.edit_text(
        "\U0001f4dd " + t("wallet.tg_enter_description", get_lang()),
        reply_markup=skip_keyboard(3),
    )


@router.message(AddWallet.starting_value)
async def add_wallet_starting(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if text == "-" or text.lower() == "skip":
        value = 0.0
    else:
        try:
            value = float(text)
        except ValueError:
            await message.answer(
                "\u26a0\ufe0f " + t("wallet.tg_invalid_number", get_lang())
            )
            return
    await state.update_data(starting_value=value)
    await state.set_state(AddWallet.description)
    await message.answer(
        "\U0001f4dd " + t("wallet.tg_enter_description", get_lang()),
        reply_markup=skip_keyboard(3),
    )


@router.callback_query(AddWallet.description, F.data == "skip_default")
async def add_wallet_skip_description(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(description="")
    data = await state.get_data()
    if data["wallet_type"] == "deposit":
        await state.set_state(AddWallet.interest_rate)
        await callback.message.edit_text(
            "\U0001f4c8 " + t("wallet.tg_enter_rate", get_lang()),
            reply_markup=cancel_keyboard(3),
        )
    else:
        await _finish_add_wallet(callback.message, state)


@router.message(AddWallet.description)
async def add_wallet_description(message: types.Message, state: FSMContext):
    desc = message.text.strip()
    if desc == "-" or desc.lower() == "skip":
        desc = ""
    await state.update_data(description=desc)
    data = await state.get_data()
    if data["wallet_type"] == "deposit":
        await state.set_state(AddWallet.interest_rate)
        await message.answer(
            "\U0001f4c8 " + t("wallet.tg_enter_rate", get_lang()),
            reply_markup=cancel_keyboard(3),
        )
    else:
        await _finish_add_wallet(message, state)


@router.message(AddWallet.interest_rate)
async def add_wallet_rate(message: types.Message, state: FSMContext):
    try:
        rate = float(message.text.strip().replace(",", "."))
        if rate <= 0:
            raise ValueError
    except (ValueError, AttributeError):
        await message.answer("\u26a0\ufe0f " + t("wallet.tg_rate_error", get_lang()))
        return
    await state.update_data(interest_rate=rate)
    await state.set_state(AddWallet.term_months)
    await message.answer(
        "\U0001f4c5 " + t("wallet.tg_enter_term", get_lang()),
        reply_markup=cancel_keyboard(3),
    )


@router.message(AddWallet.term_months)
async def add_wallet_term(message: types.Message, state: FSMContext):
    try:
        term = int(message.text.strip())
        if term <= 0:
            raise ValueError
    except (ValueError, AttributeError):
        await message.answer(
            "\u26a0\ufe0f " + t("wallet.tg_positive_integer", get_lang())
        )
        return
    await state.update_data(term_months=term)
    await state.set_state(AddWallet.capitalization)
    await message.answer(
        "\U0001f4b9 " + t("wallet.tg_capitalization", get_lang()),
        reply_markup=capitalization_keyboard(),
    )


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
    await message.edit_text(msg, reply_markup=back_to_menu(3))


# ── Edit wallet ──────────────────────────────────────────────────────


@router.callback_query(F.data.startswith("edit_w:"))
async def cb_edit_wallet(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    name = callback.data.split(":", 1)[1]
    resp = await backend.handle({"action": "get_wallet_detail", "data": {"name": name}})
    if resp["status"] == "error":
        await callback.message.answer(resp["message"], reply_markup=back_to_menu(3))
        return
    await state.clear()
    await state.update_data(edit_wallet_name=name, edit_data={}, current=resp["data"])
    await state.set_state(EditWallet.field_select)
    await callback.message.answer(
        "\u270f\ufe0f " + t("wallet.tg_editing", get_lang(), name=name),
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
                "\u2139\ufe0f " + t("wallet.tg_no_changes", get_lang()),
                reply_markup=back_to_menu(3),
            )
            await state.clear()
            return
        edit_data["name"] = name
        resp = await backend.handle({"action": "edit_wallet", "data": edit_data})
        await state.clear()
        msg = resp.get("message", "Done")
        await callback.message.answer(msg, reply_markup=back_to_menu(3))
        return

    if field == "name":
        await state.set_state(EditWallet.new_name)
        await callback.message.answer(
            "\u270f\ufe0f " + t("wallet.tg_enter_new_name", get_lang()),
            reply_markup=cancel_keyboard(3),
        )
    elif field == "currency":
        await state.set_state(EditWallet.currency)
        await callback.message.answer(
            "\U0001f4b1 " + t("wallet.tg_enter_new_currency", get_lang()),
            reply_markup=cancel_keyboard(3),
        )
    elif field == "description":
        await state.set_state(EditWallet.description)
        await callback.message.answer(
            "\U0001f4dd " + t("wallet.tg_enter_new_description", get_lang()),
            reply_markup=skip_keyboard(3),
        )


@router.message(EditWallet.new_name)
async def edit_wallet_name(message: types.Message, state: FSMContext):
    new_name = message.text.strip()
    if not new_name:
        await message.answer("\u26a0\ufe0f " + t("wallet.tg_name_empty", get_lang()))
        return
    data = await state.get_data()
    edit_data = data.get("edit_data", {})
    edit_data["new_name"] = new_name
    name = data["edit_wallet_name"]
    await state.update_data(edit_data=edit_data)
    await state.set_state(EditWallet.field_select)
    await message.answer(
        "\u2705 " + t("wallet.tg_name_changed", get_lang(), new_name=new_name),
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
        "\u2705 " + t("wallet.tg_currency_changed", get_lang(), currency=currency),
        reply_markup=edit_wallet_fields_keyboard(name),
    )


@router.callback_query(EditWallet.description, F.data == "skip_default")
async def edit_wallet_skip_desc(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    edit_data = data.get("edit_data", {})
    edit_data["description"] = ""
    name = data["edit_wallet_name"]
    await state.update_data(edit_data=edit_data)
    await state.set_state(EditWallet.field_select)
    await callback.message.edit_text(
        "\u2705 " + t("wallet.tg_description_cleared", get_lang()),
        reply_markup=edit_wallet_fields_keyboard(name),
    )


@router.message(EditWallet.description)
async def edit_wallet_desc(message: types.Message, state: FSMContext):
    desc = message.text.strip()
    if desc == "-" or desc.lower() == "skip":
        desc = ""
    data = await state.get_data()
    edit_data = data.get("edit_data", {})
    edit_data["description"] = desc
    name = data["edit_wallet_name"]
    await state.update_data(edit_data=edit_data)
    await state.set_state(EditWallet.field_select)
    await message.answer(
        "\u2705 " + t("wallet.tg_description_updated", get_lang()),
        reply_markup=edit_wallet_fields_keyboard(name),
    )


# ── Delete wallet ────────────────────────────────────────────────────


@router.callback_query(F.data.startswith("del_w:"))
async def cb_delete_wallet(callback: types.CallbackQuery):
    await callback.answer()
    name = callback.data.split(":", 1)[1]
    await callback.message.answer(
        "\U0001f5d1\ufe0f " + t("wallet.tg_confirm_delete", get_lang(), name=name),
        reply_markup=confirm_keyboard("delw", name, page=3),
    )


@router.callback_query(F.data.startswith("confirm_delw:"))
async def cb_confirm_delete_wallet(callback: types.CallbackQuery):
    await callback.answer()
    name = callback.data.split(":")[1]
    resp = await backend.handle({"action": "delete_wallet", "data": {"name": name}})
    msg = resp.get("message", "Done")
    await callback.message.answer(msg, reply_markup=back_to_menu(3))
