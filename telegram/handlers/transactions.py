"""Transaction handlers: add, show, edit, delete."""

from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from telegram.backend import backend
from telegram.keyboards import (
    category_keyboard,
    cancel_keyboard,
    back_to_menu,
    transaction_actions_keyboard,
    edit_transaction_fields_keyboard,
    confirm_keyboard,
)
from telegram.states import AddTransaction, EditTransaction
from telegram.utils import fmt_transaction, _to_md2

router = Router()


# ── Add transaction ──────────────────────────────────────────────────


@router.message(Command("income"))
async def cmd_income(message: types.Message, state: FSMContext):
    await _start_add(message, state, "income")


@router.message(Command("expense"))
async def cmd_expense(message: types.Message, state: FSMContext):
    await _start_add(message, state, "expense")


@router.callback_query(F.data == "add_income")
async def cb_add_income(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await _start_add(callback.message, state, "income")


@router.callback_query(F.data == "add_expense")
async def cb_add_expense(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await _start_add(callback.message, state, "expense")


async def _start_add(message: types.Message, state: FSMContext, tt: str):
    await state.clear()
    resp = await backend.handle(
        {"action": "get_categories", "data": {"transaction_type": tt}}
    )
    if resp["status"] == "error":
        await message.answer(resp["message"])
        return
    categories = resp["data"]["categories"]
    await state.update_data(transaction_type=tt, categories=categories)
    await state.set_state(AddTransaction.amount)
    label = "Income" if tt == "income" else "Expense"
    await message.answer(
        f"Adding {label}. Enter amount:",
        reply_markup=cancel_keyboard(),
    )


@router.message(AddTransaction.amount)
async def add_tx_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        if amount <= 0:
            raise ValueError
    except (ValueError, AttributeError):
        await message.answer("Please enter a positive number.")
        return
    await state.update_data(amount=amount)
    data = await state.get_data()
    await state.set_state(AddTransaction.category)
    await message.answer(
        "Select category:", reply_markup=category_keyboard(data["categories"])
    )


@router.callback_query(AddTransaction.category, F.data.startswith("cat:"))
async def add_tx_category(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    cat = callback.data.split(":", 1)[1]
    if cat == "__new__":
        await state.set_state(AddTransaction.new_category)
        await callback.message.answer(
            "Enter new category name:", reply_markup=cancel_keyboard()
        )
        return
    await state.update_data(category=cat)
    await state.set_state(AddTransaction.description)
    await callback.message.answer(
        "Enter description (or send `-` to skip):", reply_markup=cancel_keyboard()
    )


@router.message(AddTransaction.new_category)
async def add_tx_new_cat(message: types.Message, state: FSMContext):
    cat = message.text.strip()
    if not cat:
        await message.answer("Category name cannot be empty.")
        return
    await state.update_data(category=cat)
    await state.set_state(AddTransaction.description)
    await message.answer(
        "Enter description (or send `-` to skip):", reply_markup=cancel_keyboard()
    )


@router.message(AddTransaction.description)
async def add_tx_description(message: types.Message, state: FSMContext):
    desc = message.text.strip()
    if desc == "-":
        desc = ""
    await state.update_data(description=desc)
    await state.set_state(AddTransaction.date)
    await message.answer(
        "Enter date (YYYY-MM-DD) or send `-` for today:",
        reply_markup=cancel_keyboard(),
    )


@router.message(AddTransaction.date)
async def add_tx_date(message: types.Message, state: FSMContext):
    text = message.text.strip()
    date_val = None if text == "-" else text
    data = await state.get_data()
    form = {
        "transaction_type": data["transaction_type"],
        "amount": data["amount"],
        "category": data["category"],
        "description": data.get("description", ""),
        "date": date_val,
    }
    resp = await backend.handle({"action": "add_transaction", "data": form})
    await state.clear()
    if resp["status"] == "success":
        await message.answer(
            f"Transaction added: {data['amount']:.2f} in {data['category']}",
            reply_markup=back_to_menu(),
        )
    else:
        await message.answer(resp["message"], reply_markup=back_to_menu())


# ── Show transaction ─────────────────────────────────────────────────


@router.message(Command("show"))
async def cmd_show(message: types.Message):
    parts = message.text.strip().split()
    if len(parts) < 2:
        await message.answer("Usage: /show <index>")
        return
    try:
        index = int(parts[1])
    except ValueError:
        await message.answer("Index must be a number.")
        return
    await _show_transaction(message, index)


@router.callback_query(F.data.startswith("show_tx:"))
async def cb_show_tx(callback: types.CallbackQuery):
    await callback.answer()
    index = int(callback.data.split(":")[1])
    await _show_transaction(callback.message, index)


async def _show_transaction(message: types.Message, index: int):
    resp = await backend.handle({"action": "get_transaction", "data": {"index": index}})
    if resp["status"] == "error":
        await message.answer(resp["message"], reply_markup=back_to_menu())
        return
    text = fmt_transaction(resp["data"])
    await message.answer(
        text,
        parse_mode="MarkdownV2",
        reply_markup=transaction_actions_keyboard(index),
    )


# ── Edit transaction ─────────────────────────────────────────────────


@router.callback_query(F.data.startswith("edit_tx:"))
async def cb_edit_tx(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    index = int(callback.data.split(":")[1])
    resp = await backend.handle({"action": "get_transaction", "data": {"index": index}})
    if resp["status"] == "error":
        await callback.message.answer(resp["message"], reply_markup=back_to_menu())
        return
    current = resp["data"]
    await state.clear()
    await state.update_data(
        edit_index=index,
        edit_data={},
        current=current,
    )
    await state.set_state(EditTransaction.field_select)
    is_transfer = current.get("is_transfer", False)
    await callback.message.answer(
        f"Editing transaction #{index}. Select field to edit:",
        reply_markup=edit_transaction_fields_keyboard(index, is_transfer),
    )


@router.callback_query(EditTransaction.field_select, F.data.startswith("etf:"))
async def cb_edit_tx_field(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    parts = callback.data.split(":")
    index = int(parts[1])
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
        edit_data["index"] = index
        resp = await backend.handle({"action": "edit_transaction", "data": edit_data})
        await state.clear()
        msg = resp.get("message", "Done")
        await callback.message.answer(msg, reply_markup=back_to_menu())
        return

    if field == "amount":
        await state.set_state(EditTransaction.amount)
        await callback.message.answer(
            "Enter new amount:", reply_markup=cancel_keyboard()
        )
    elif field == "category":
        current = data["current"]
        tt = current.get("transaction_type", "expense")
        tt_name = "income" if tt == "+" else "expense"
        cat_resp = await backend.handle(
            {"action": "get_categories", "data": {"transaction_type": tt_name}}
        )
        cats = cat_resp["data"]["categories"]
        await state.update_data(categories=cats)
        await state.set_state(EditTransaction.category)
        await callback.message.answer(
            "Select new category:", reply_markup=category_keyboard(cats)
        )
    elif field == "description":
        await state.set_state(EditTransaction.description)
        await callback.message.answer(
            "Enter new description (or `-` to clear):", reply_markup=cancel_keyboard()
        )
    elif field == "date":
        await state.set_state(EditTransaction.date)
        await callback.message.answer(
            "Enter new date (YYYY-MM-DD):", reply_markup=cancel_keyboard()
        )


@router.message(EditTransaction.amount)
async def edit_tx_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        if amount <= 0:
            raise ValueError
    except (ValueError, AttributeError):
        await message.answer("Please enter a positive number.")
        return
    data = await state.get_data()
    edit_data = data.get("edit_data", {})
    edit_data["amount"] = amount
    index = data["edit_index"]
    current = data["current"]
    await state.update_data(edit_data=edit_data)
    await state.set_state(EditTransaction.field_select)
    await message.answer(
        f"Amount updated to {amount:.2f}. Select another field or Save:",
        reply_markup=edit_transaction_fields_keyboard(
            index, current.get("is_transfer", False)
        ),
    )


@router.callback_query(EditTransaction.category, F.data.startswith("cat:"))
async def edit_tx_category(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    cat = callback.data.split(":", 1)[1]
    if cat == "__new__":
        await state.set_state(EditTransaction.new_category)
        await callback.message.answer(
            "Enter new category name:", reply_markup=cancel_keyboard()
        )
        return
    data = await state.get_data()
    edit_data = data.get("edit_data", {})
    edit_data["category"] = cat
    index = data["edit_index"]
    current = data["current"]
    await state.update_data(edit_data=edit_data)
    await state.set_state(EditTransaction.field_select)
    await callback.message.answer(
        f"Category updated to {cat}. Select another field or Save:",
        reply_markup=edit_transaction_fields_keyboard(
            index, current.get("is_transfer", False)
        ),
    )


@router.message(EditTransaction.new_category)
async def edit_tx_new_cat(message: types.Message, state: FSMContext):
    cat = message.text.strip()
    if not cat:
        await message.answer("Category name cannot be empty.")
        return
    data = await state.get_data()
    edit_data = data.get("edit_data", {})
    edit_data["category"] = cat
    index = data["edit_index"]
    current = data["current"]
    await state.update_data(edit_data=edit_data)
    await state.set_state(EditTransaction.field_select)
    await message.answer(
        f"Category set to {cat}. Select another field or Save:",
        reply_markup=edit_transaction_fields_keyboard(
            index, current.get("is_transfer", False)
        ),
    )


@router.message(EditTransaction.description)
async def edit_tx_description(message: types.Message, state: FSMContext):
    desc = message.text.strip()
    if desc == "-":
        desc = ""
    data = await state.get_data()
    edit_data = data.get("edit_data", {})
    edit_data["description"] = desc
    index = data["edit_index"]
    current = data["current"]
    await state.update_data(edit_data=edit_data)
    await state.set_state(EditTransaction.field_select)
    await message.answer(
        "Description updated. Select another field or Save:",
        reply_markup=edit_transaction_fields_keyboard(
            index, current.get("is_transfer", False)
        ),
    )


@router.message(EditTransaction.date)
async def edit_tx_date(message: types.Message, state: FSMContext):
    date_val = message.text.strip()
    data = await state.get_data()
    edit_data = data.get("edit_data", {})
    edit_data["date"] = date_val
    index = data["edit_index"]
    current = data["current"]
    await state.update_data(edit_data=edit_data)
    await state.set_state(EditTransaction.field_select)
    await message.answer(
        f"Date updated to {date_val}. Select another field or Save:",
        reply_markup=edit_transaction_fields_keyboard(
            index, current.get("is_transfer", False)
        ),
    )


# ── Delete transaction ───────────────────────────────────────────────


@router.callback_query(F.data.startswith("del_tx:"))
async def cb_delete_tx(callback: types.CallbackQuery):
    await callback.answer()
    index = int(callback.data.split(":")[1])
    resp = await backend.handle({"action": "get_transaction", "data": {"index": index}})
    if resp["status"] == "error":
        await callback.message.answer(resp["message"], reply_markup=back_to_menu())
        return
    text = fmt_transaction(resp["data"])
    warning = ""
    if resp["data"].get("is_transfer"):
        warning = _to_md2(
            "\nThis is a transfer. Deleting will also remove the linked transaction."
        )
    suffix = _to_md2("\nDelete this transaction?")
    await callback.message.answer(
        f"{text}\n{warning}{suffix}",
        parse_mode="MarkdownV2",
        reply_markup=confirm_keyboard("deltx", str(index)),
    )


@router.callback_query(F.data.startswith("confirm_deltx:"))
async def cb_confirm_delete_tx(callback: types.CallbackQuery):
    await callback.answer()
    index = int(callback.data.split(":")[1])
    resp = await backend.handle(
        {"action": "delete_transaction", "data": {"index": index}}
    )
    msg = resp.get("message", "Done")
    await callback.message.answer(msg, reply_markup=back_to_menu())


# ── Text-based commands (show N, edit N, delete N) ───────────────────


@router.message(Command("edit"))
async def cmd_edit(message: types.Message, state: FSMContext):
    parts = message.text.strip().split()
    if len(parts) < 2:
        await message.answer("Usage: /edit <index>")
        return
    try:
        index = int(parts[1])
    except ValueError:
        await message.answer("Index must be a number.")
        return

    # Reuse callback logic
    class FakeCallback:
        data = f"edit_tx:{index}"

        async def answer(self):
            pass

        message_obj = message

    fc = FakeCallback()
    fc.message = message
    await cb_edit_tx(fc, state)


@router.message(Command("delete"))
async def cmd_delete(message: types.Message):
    parts = message.text.strip().split()
    if len(parts) < 2:
        await message.answer("Usage: /delete <index>")
        return
    try:
        index = int(parts[1])
    except ValueError:
        await message.answer("Index must be a number.")
        return

    class FakeCallback:
        data = f"del_tx:{index}"

        async def answer(self):
            pass

    fc = FakeCallback()
    fc.message = message
    await cb_delete_tx(fc)
