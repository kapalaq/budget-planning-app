"""Bill handlers."""

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from languages import t
from telegram.backend import backend, get_lang
from telegram.keyboards import (
    back_to_menu,
    bill_actions_keyboard,
    bill_list_keyboard,
    bill_menu_keyboard,
    cancel_keyboard,
    confirm_keyboard,
    parse_menu_page,
    skip_keyboard,
)
from telegram.states import AddBill, PayBill
from telegram.utils import fmt_bill_detail, fmt_bills

router = Router()


# ── Bill menu ────────────────────────────────────────────────────────


@router.callback_query(F.data.startswith("bills_menu"))
async def cb_bills_menu(callback: types.CallbackQuery):
    await callback.answer()
    page = parse_menu_page(callback.data, default=3)
    await callback.message.edit_text(
        "\U0001f4cb " + t("bill.tg_title", get_lang()),
        reply_markup=bill_menu_keyboard(menu_page=page),
    )


# ── List bills ───────────────────────────────────────────────────────


@router.callback_query(F.data.startswith("bills:"))
async def cb_bills_list(callback: types.CallbackQuery):
    await callback.answer()
    filter_type = callback.data.split(":", 1)[1]
    resp = await backend.handle(
        {"action": "get_bills", "data": {"filter": filter_type}}
    )
    if resp["status"] == "error":
        await callback.message.edit_text(resp["message"], reply_markup=back_to_menu(3))
        return
    bills = resp["data"]["bills"]
    label = filter_type.capitalize()
    text = fmt_bills(bills, label, lang=get_lang())
    await callback.message.edit_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=bill_list_keyboard(bills),
    )


# ── Bill detail ──────────────────────────────────────────────────────


@router.callback_query(F.data.startswith("bdet:"))
async def cb_bill_detail(callback: types.CallbackQuery):
    await callback.answer()
    name = callback.data.split(":", 1)[1]
    resp = await backend.handle({"action": "get_bill_detail", "data": {"name": name}})
    if resp["status"] == "error":
        await callback.message.edit_text(resp["message"], reply_markup=back_to_menu(3))
        return
    data = resp["data"]
    status = data.get("bill", {}).get("status", "active")
    text = fmt_bill_detail(data, lang=get_lang())
    await callback.message.edit_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=bill_actions_keyboard(name, status),
    )


# ── Add bill ─────────────────────────────────────────────────────────


@router.callback_query(F.data == "add_bill_start")
async def cb_add_bill_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await state.set_state(AddBill.name)
    await callback.message.edit_text(
        "\U0001f4cb " + t("bill.tg_enter_name", get_lang()),
        reply_markup=cancel_keyboard(3),
    )


@router.message(AddBill.name)
async def add_bill_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    if not name:
        await message.answer("\u26a0\ufe0f " + t("wallet.tg_name_empty", get_lang()))
        return
    await state.update_data(name=name)
    await state.set_state(AddBill.target)
    await message.answer(
        "\U0001f4b0 " + t("bill.tg_enter_target", get_lang()),
        reply_markup=cancel_keyboard(3),
    )


@router.message(AddBill.target)
async def add_bill_target(message: types.Message, state: FSMContext):
    try:
        target = float(message.text.strip().replace(",", "."))
        if target <= 0:
            raise ValueError
    except (ValueError, AttributeError):
        await message.answer(
            "\u26a0\ufe0f " + t("transaction.tg_positive_number", get_lang())
        )
        return
    await state.update_data(target=target)
    await state.set_state(AddBill.currency)
    await message.answer(
        "\U0001f4b1 " + t("bill.tg_enter_currency", get_lang()),
        reply_markup=skip_keyboard(3),
    )


@router.callback_query(AddBill.currency, F.data == "skip_default")
async def add_bill_skip_currency(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(currency="KZT")
    await state.set_state(AddBill.description)
    await callback.message.edit_text(
        "\U0001f4dd " + t("bill.tg_enter_description", get_lang()),
        reply_markup=skip_keyboard(3),
    )


@router.message(AddBill.currency)
async def add_bill_currency(message: types.Message, state: FSMContext):
    text = message.text.strip()
    currency = "KZT" if text == "-" or text.lower() == "skip" else text.upper()
    await state.update_data(currency=currency)
    await state.set_state(AddBill.description)
    await message.answer(
        "\U0001f4dd " + t("bill.tg_enter_description", get_lang()),
        reply_markup=skip_keyboard(3),
    )


@router.callback_query(AddBill.description, F.data == "skip_default")
async def add_bill_skip_desc(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(description="")
    await _finish_add_bill(callback.message, state)


@router.message(AddBill.description)
async def add_bill_description(message: types.Message, state: FSMContext):
    desc = message.text.strip()
    if desc == "-" or desc.lower() == "skip":
        desc = ""
    await state.update_data(description=desc)
    await _finish_add_bill(message, state)


async def _finish_add_bill(message: types.Message, state: FSMContext):
    data = await state.get_data()
    form = {
        "name": data["name"],
        "target": data["target"],
        "currency": data.get("currency", "KZT"),
        "goal_description": data.get("description") or data["name"],
    }
    resp = await backend.handle({"action": "add_bill", "data": form})
    await state.clear()
    msg = resp.get("message", "Done")
    await message.answer(msg, reply_markup=back_to_menu(3))


# ── Pay bill ─────────────────────────────────────────────────────────


@router.callback_query(F.data.startswith("bpay:"))
async def cb_pay_bill(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    name = callback.data.split(":", 1)[1]
    await state.clear()
    await state.update_data(bill_name=name)
    await state.set_state(PayBill.amount)
    await callback.message.edit_text(
        "\U0001f4b0 " + t("bill.tg_pay_amount", get_lang(), name=name),
        reply_markup=cancel_keyboard(3),
    )


@router.message(PayBill.amount)
async def pay_bill_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip().replace(",", "."))
        if amount <= 0:
            raise ValueError
    except (ValueError, AttributeError):
        await message.answer(
            "\u26a0\ufe0f " + t("transaction.tg_positive_number", get_lang())
        )
        return
    data = await state.get_data()
    bill_name = data["bill_name"]
    resp = await backend.handle(
        {
            "action": "save_to_bill",
            "data": {
                "bill_name": bill_name,
                "amount": amount,
                "description": f"Payment to {bill_name}",
            },
        }
    )
    await state.clear()
    msg = resp.get("message", "Done")
    await message.answer(msg, reply_markup=back_to_menu(3))


# ── Complete bill ────────────────────────────────────────────────────


@router.callback_query(F.data.startswith("bcomplete:"))
async def cb_complete_bill(callback: types.CallbackQuery):
    await callback.answer()
    name = callback.data.split(":", 1)[1]
    resp = await backend.handle({"action": "complete_bill", "data": {"name": name}})
    msg = resp.get("message", "Done")
    await callback.message.edit_text(msg, reply_markup=back_to_menu(3))


# ── Hide bill ────────────────────────────────────────────────────────


@router.callback_query(F.data.startswith("bhide:"))
async def cb_hide_bill(callback: types.CallbackQuery):
    await callback.answer()
    name = callback.data.split(":", 1)[1]
    resp = await backend.handle({"action": "hide_bill", "data": {"name": name}})
    msg = resp.get("message", "Done")
    await callback.message.edit_text(msg, reply_markup=back_to_menu(3))


# ── Reactivate bill ──────────────────────────────────────────────────


@router.callback_query(F.data.startswith("breactivate:"))
async def cb_reactivate_bill(callback: types.CallbackQuery):
    await callback.answer()
    name = callback.data.split(":", 1)[1]
    resp = await backend.handle({"action": "reactivate_bill", "data": {"name": name}})
    msg = resp.get("message", "Done")
    await callback.message.edit_text(msg, reply_markup=back_to_menu(3))


# ── Delete bill ─────────────────────────────────────────────────────


@router.callback_query(F.data.startswith("bdel:"))
async def cb_delete_bill(callback: types.CallbackQuery):
    await callback.answer()
    name = callback.data.split(":", 1)[1]
    await callback.message.edit_text(
        "\U0001f5d1\ufe0f " + t("bill.tg_confirm_delete", get_lang(), name=name),
        reply_markup=confirm_keyboard("delbill", name, page=3),
    )


@router.callback_query(F.data.startswith("confirm_delbill:"))
async def cb_confirm_delete_bill(callback: types.CallbackQuery):
    await callback.answer()
    name = callback.data.split(":", 1)[1]
    resp = await backend.handle({"action": "delete_bill", "data": {"name": name}})
    msg = resp.get("message", "Done")
    await callback.message.edit_text(msg, reply_markup=back_to_menu(3))
