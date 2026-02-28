"""Filter handlers."""

from aiogram import Router, F, types
from aiogram.filters import Command

from telegram.backend import backend
from telegram.keyboards import (
    filter_menu_keyboard,
    date_filter_keyboard,
    type_filter_keyboard,
    amount_filter_keyboard,
    back_to_menu,
)
from telegram.utils import fmt_filters

router = Router()


@router.message(Command("filters"))
async def cmd_filters(message: types.Message):
    await message.answer("Filter options:", reply_markup=filter_menu_keyboard())


@router.callback_query(F.data == "filters")
async def cb_filters(callback: types.CallbackQuery):
    await callback.answer()
    try:
        await callback.message.edit_text(
            "Filter options:", reply_markup=filter_menu_keyboard()
        )
    except Exception:
        await callback.message.answer(
            "Filter options:", reply_markup=filter_menu_keyboard()
        )


# ── Date filter ──────────────────────────────────────────────────────


@router.callback_query(F.data == "filter:date")
async def cb_filter_date(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "Select date filter:", reply_markup=date_filter_keyboard()
    )


@router.callback_query(F.data.startswith("df:"))
async def cb_date_filter_choice(callback: types.CallbackQuery):
    await callback.answer()
    filter_type = callback.data.split(":")[1]
    resp = await backend.handle(
        {"action": "add_filter", "data": {"filter_type": filter_type}}
    )
    msg = resp.get("message", "Done")
    await callback.message.answer(msg, reply_markup=back_to_menu())


# ── Type filter ──────────────────────────────────────────────────────


@router.callback_query(F.data == "filter:type")
async def cb_filter_type(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "Select type filter:", reply_markup=type_filter_keyboard()
    )


@router.callback_query(F.data.startswith("tf:"))
async def cb_type_filter_choice(callback: types.CallbackQuery):
    await callback.answer()
    filter_type = callback.data.split(":")[1]
    resp = await backend.handle(
        {"action": "add_filter", "data": {"filter_type": filter_type}}
    )
    msg = resp.get("message", "Done")
    await callback.message.answer(msg, reply_markup=back_to_menu())


# ── Amount filter ────────────────────────────────────────────────────


@router.callback_query(F.data == "filter:amount")
async def cb_filter_amount(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "Select amount filter:", reply_markup=amount_filter_keyboard()
    )


@router.callback_query(F.data.startswith("af:"))
async def cb_amount_filter_choice(callback: types.CallbackQuery):
    await callback.answer()
    filter_type = callback.data.split(":")[1]
    resp = await backend.handle(
        {"action": "add_filter", "data": {"filter_type": filter_type}}
    )
    msg = resp.get("message", "Done")
    await callback.message.answer(msg, reply_markup=back_to_menu())


# ── Category filter (simplified: just lists categories as buttons) ───


@router.callback_query(F.data == "filter:category")
async def cb_filter_category(callback: types.CallbackQuery):
    await callback.answer()
    # Get all categories
    resp1 = await backend.handle(
        {"action": "get_categories", "data": {"transaction_type": "income"}}
    )
    resp2 = await backend.handle(
        {"action": "get_categories", "data": {"transaction_type": "expense"}}
    )
    income_cats = set(resp1["data"]["categories"])
    expense_cats = set(resp2["data"]["categories"])
    all_cats = sorted(income_cats | expense_cats | {"Transfer"})

    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    rows = []
    for i in range(0, len(all_cats), 2):
        row = [
            InlineKeyboardButton(text=c, callback_data=f"catf:{c}")
            for c in all_cats[i : i + 2]
        ]
        rows.append(row)
    rows.append([InlineKeyboardButton(text="Cancel", callback_data="filters")])
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    await callback.message.answer(
        "Select category to filter by (include only):", reply_markup=kb
    )


@router.callback_query(F.data.startswith("catf:"))
async def cb_cat_filter_choice(callback: types.CallbackQuery):
    await callback.answer()
    cat = callback.data.split(":", 1)[1]
    resp = await backend.handle(
        {
            "action": "add_filter",
            "data": {
                "filter_type": "category",
                "categories": [cat],
                "mode": "include",
            },
        }
    )
    msg = resp.get("message", "Done")
    await callback.message.answer(msg, reply_markup=back_to_menu())


# ── Description filter ───────────────────────────────────────────────


@router.callback_query(F.data == "filter:description")
async def cb_filter_description(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "Send the search text to filter descriptions by:",
        reply_markup=back_to_menu(),
    )
    # We'll handle this via a special text handler in bot.py if needed
    # For simplicity, using a direct approach


# ── View active / Clear all ──────────────────────────────────────────


@router.callback_query(F.data == "filter:view_active")
async def cb_view_active_filters(callback: types.CallbackQuery):
    await callback.answer()
    resp = await backend.handle({"action": "get_active_filters", "data": {}})
    if resp["status"] == "error":
        await callback.message.answer(resp["message"], reply_markup=back_to_menu())
        return
    text = fmt_filters(resp["data"]["filters"])
    await callback.message.answer(text, reply_markup=filter_menu_keyboard())


@router.callback_query(F.data == "filter:clear_all")
async def cb_clear_all_filters(callback: types.CallbackQuery):
    await callback.answer()
    resp = await backend.handle({"action": "clear_filters", "data": {}})
    msg = resp.get("message", "Done")
    await callback.message.answer(msg, reply_markup=back_to_menu())
