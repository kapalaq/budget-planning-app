"""Recurring transaction handlers."""

from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from telegram.backend import backend
from telegram.keyboards import (
    back_to_menu,
    cancel_keyboard,
    category_keyboard,
    frequency_keyboard,
    end_condition_keyboard,
    recurring_actions_keyboard,
    delete_recurring_keyboard,
    edit_recurring_keyboard,
)
from telegram.states import AddRecurring, DeleteRecurring
from telegram.utils import fmt_recurring_list

router = Router()


# ── List recurring ───────────────────────────────────────────────────


@router.message(Command("recurring"))
async def cmd_recurring(message: types.Message):
    await _show_recurring_list(message)


@router.callback_query(F.data == "recurring_list")
async def cb_recurring_list(callback: types.CallbackQuery):
    await callback.answer()
    await _show_recurring_list(callback.message)


async def _show_recurring_list(message: types.Message):
    resp = await backend.handle({"action": "get_recurring_list", "data": {}})
    items = resp["data"]["recurring_transactions"]
    text = fmt_recurring_list(items)

    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    rows = []
    for i, r in enumerate(items, 1):
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{i}. {r['summary'][:40]}",
                    callback_data=f"show_rec:{i}",
                )
            ]
        )
    rows.append([InlineKeyboardButton(text="<< Menu", callback_data="dashboard")])
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    await message.answer(text, parse_mode="MarkdownV2", reply_markup=kb)


# ── Show recurring detail ────────────────────────────────────────────


@router.callback_query(F.data.startswith("show_rec:"))
async def cb_show_recurring(callback: types.CallbackQuery):
    await callback.answer()
    index = int(callback.data.split(":")[1])
    resp = await backend.handle(
        {"action": "get_recurring_detail", "data": {"index": index}}
    )
    if resp["status"] == "error":
        await callback.message.answer(resp["message"], reply_markup=back_to_menu())
        return
    detail = resp["data"].get("detail", str(resp["data"]))
    await callback.message.answer(
        detail, reply_markup=recurring_actions_keyboard(index)
    )


# ── Add recurring ────────────────────────────────────────────────────


@router.callback_query(F.data == "add_recurring_income")
async def cb_add_rec_income(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await _start_add_recurring(callback.message, state, "income")


@router.callback_query(F.data == "add_recurring_expense")
async def cb_add_rec_expense(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await _start_add_recurring(callback.message, state, "expense")


async def _start_add_recurring(message: types.Message, state: FSMContext, tt: str):
    await state.clear()
    resp = await backend.handle(
        {"action": "get_categories", "data": {"transaction_type": tt}}
    )
    if resp["status"] == "error":
        await message.answer(resp["message"])
        return
    categories = resp["data"]["categories"]
    await state.update_data(transaction_type=tt, categories=categories)
    await state.set_state(AddRecurring.amount)
    label = "Income" if tt == "income" else "Expense"
    await message.answer(
        f"Adding recurring {label}.\nEnter amount:", reply_markup=cancel_keyboard()
    )


@router.message(AddRecurring.amount)
async def rec_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        if amount <= 0:
            raise ValueError
    except (ValueError, AttributeError):
        await message.answer("Please enter a positive number.")
        return
    await state.update_data(amount=amount)
    data = await state.get_data()
    await state.set_state(AddRecurring.category)
    await message.answer(
        "Select category:", reply_markup=category_keyboard(data["categories"])
    )


@router.callback_query(AddRecurring.category, F.data.startswith("cat:"))
async def rec_category(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    cat = callback.data.split(":", 1)[1]
    if cat == "__new__":
        await state.set_state(AddRecurring.new_category)
        await callback.message.answer(
            "Enter new category name:", reply_markup=cancel_keyboard()
        )
        return
    await state.update_data(category=cat)
    await state.set_state(AddRecurring.description)
    await callback.message.answer(
        "Enter description (or `-` to skip):", reply_markup=cancel_keyboard()
    )


@router.message(AddRecurring.new_category)
async def rec_new_cat(message: types.Message, state: FSMContext):
    cat = message.text.strip()
    if not cat:
        await message.answer("Category name cannot be empty.")
        return
    await state.update_data(category=cat)
    await state.set_state(AddRecurring.description)
    await message.answer(
        "Enter description (or `-` to skip):", reply_markup=cancel_keyboard()
    )


@router.message(AddRecurring.description)
async def rec_description(message: types.Message, state: FSMContext):
    desc = message.text.strip()
    if desc == "-":
        desc = ""
    await state.update_data(description=desc)
    await state.set_state(AddRecurring.start_date)
    await message.answer(
        "Enter start date (YYYY-MM-DD) or `-` for today:",
        reply_markup=cancel_keyboard(),
    )


@router.message(AddRecurring.start_date)
async def rec_start_date(message: types.Message, state: FSMContext):
    text = message.text.strip()
    date_val = None if text == "-" else text
    await state.update_data(start_date=date_val)
    await state.set_state(AddRecurring.frequency)
    await message.answer("Select frequency:", reply_markup=frequency_keyboard())


@router.callback_query(AddRecurring.frequency, F.data.startswith("freq:"))
async def rec_frequency(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    freq = callback.data.split(":")[1]
    await state.update_data(frequency=freq)
    await state.set_state(AddRecurring.interval)
    await callback.message.answer(
        f"Enter interval (every N {freq} periods, or `-` for 1):",
        reply_markup=cancel_keyboard(),
    )


@router.message(AddRecurring.interval)
async def rec_interval(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if text == "-":
        interval = 1
    else:
        try:
            interval = int(text)
            if interval <= 0:
                raise ValueError
        except ValueError:
            await message.answer("Please enter a positive integer.")
            return
    await state.update_data(interval=interval)
    await state.set_state(AddRecurring.end_condition)
    await message.answer("Select end condition:", reply_markup=end_condition_keyboard())


@router.callback_query(AddRecurring.end_condition, F.data.startswith("endc:"))
async def rec_end_condition(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    endc = callback.data.split(":")[1]
    await state.update_data(end_condition=endc)

    if endc == "never":
        await _finish_add_recurring(callback.message, state)
    elif endc == "on_date":
        await state.set_state(AddRecurring.end_date)
        await callback.message.answer(
            "Enter end date (YYYY-MM-DD):", reply_markup=cancel_keyboard()
        )
    elif endc == "after_count":
        await state.set_state(AddRecurring.end_count)
        await callback.message.answer(
            "Enter number of occurrences:", reply_markup=cancel_keyboard()
        )


@router.message(AddRecurring.end_date)
async def rec_end_date(message: types.Message, state: FSMContext):
    date_val = message.text.strip()
    await state.update_data(end_date=date_val)
    await _finish_add_recurring(message, state)


@router.message(AddRecurring.end_count)
async def rec_end_count(message: types.Message, state: FSMContext):
    try:
        count = int(message.text.strip())
        if count <= 0:
            raise ValueError
    except (ValueError, AttributeError):
        await message.answer("Please enter a positive integer.")
        return
    await state.update_data(max_occurrences=count)
    await _finish_add_recurring(message, state)


async def _finish_add_recurring(message: types.Message, state: FSMContext):
    data = await state.get_data()
    rule = {
        "frequency": data["frequency"],
        "interval": data.get("interval", 1),
        "end_condition": data["end_condition"],
    }
    if data["end_condition"] == "on_date":
        rule["end_date"] = data["end_date"]
    elif data["end_condition"] == "after_count":
        rule["max_occurrences"] = data["max_occurrences"]

    form = {
        "transaction_type": data["transaction_type"],
        "amount": data["amount"],
        "category": data["category"],
        "description": data.get("description", ""),
        "start_date": data.get("start_date"),
        "recurrence_rule": rule,
    }
    resp = await backend.handle({"action": "add_recurring", "data": form})
    await state.clear()
    msg = resp.get("message", "Done")
    await message.answer(msg, reply_markup=back_to_menu())


# ── Edit recurring ───────────────────────────────────────────────────


@router.callback_query(F.data.startswith("edit_rec:"))
async def cb_edit_recurring(callback: types.CallbackQuery):
    await callback.answer()
    index = int(callback.data.split(":")[1])
    await callback.message.answer(
        f"Edit recurring #{index}:", reply_markup=edit_recurring_keyboard(index)
    )


@router.callback_query(F.data.startswith("erec:"))
async def cb_edit_rec_action(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    parts = callback.data.split(":")
    index = int(parts[1])
    action = parts[2]

    if action == "toggle":
        resp = await backend.handle(
            {
                "action": "edit_recurring",
                "data": {"index": index, "edit_action": "toggle_active"},
            }
        )
        msg = resp.get("message", "Done")
        await callback.message.answer(msg, reply_markup=back_to_menu())
    elif action == "skip":
        await state.clear()
        await state.update_data(rec_index=index)
        await state.set_state(DeleteRecurring.delete_option)
        await callback.message.answer(
            "Enter date to skip (YYYY-MM-DD):", reply_markup=cancel_keyboard()
        )
    elif action == "template":
        # Simplified: send edit data for amount change
        await state.clear()
        await state.update_data(rec_index=index, rec_edit={})

        resp = await backend.handle(
            {"action": "get_recurring_detail", "data": {"index": index}}
        )
        if resp["status"] == "error":
            await callback.message.answer(resp["message"], reply_markup=back_to_menu())
            return

        await callback.message.answer(
            "Enter new amount (or `-` to keep current):",
            reply_markup=cancel_keyboard(),
        )
        await state.set_state(AddRecurring.amount)
        await state.update_data(
            editing_template=True,
            transaction_type=resp["data"].get("transaction_type", "expense"),
        )


# Handle skip date entry (reusing DeleteRecurring.delete_option state)
@router.message(DeleteRecurring.delete_option)
async def skip_date_entry(message: types.Message, state: FSMContext):
    data = await state.get_data()
    # Check if this is a skip date or delete option
    text = message.text.strip()
    index = data.get("rec_index")
    if index and "-" in text:
        # It's a date for skip
        resp = await backend.handle(
            {
                "action": "edit_recurring",
                "data": {
                    "index": index,
                    "edit_action": "skip_date",
                    "date": text,
                },
            }
        )
        await state.clear()
        msg = resp.get("message", "Done")
        await message.answer(msg, reply_markup=back_to_menu())


# ── Delete recurring ─────────────────────────────────────────────────


@router.callback_query(F.data.startswith("del_rec:"))
async def cb_delete_recurring(callback: types.CallbackQuery):
    await callback.answer()
    index = int(callback.data.split(":")[1])
    await callback.message.answer(
        f"Delete recurring #{index}. Choose scope:",
        reply_markup=delete_recurring_keyboard(index),
    )


@router.callback_query(F.data.startswith("delrec_opt:"))
async def cb_delete_rec_opt(callback: types.CallbackQuery):
    await callback.answer()
    parts = callback.data.split(":")
    index = int(parts[1])
    option = int(parts[2])
    resp = await backend.handle(
        {
            "action": "delete_recurring",
            "data": {"index": index, "delete_option": option},
        }
    )
    msg = resp.get("message", "Done")
    await callback.message.answer(msg, reply_markup=back_to_menu())
