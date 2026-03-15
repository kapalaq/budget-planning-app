"""Filter handlers."""

from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from telegram.backend import backend
from telegram.keyboards import (
    filter_menu_keyboard,
    date_filter_keyboard,
    type_filter_keyboard,
    amount_filter_keyboard,
    back_to_menu,
)
from telegram.states import FilterInput
from telegram.utils import fmt_filters

router = Router()


@router.message(Command("filters"))
async def cmd_filters(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "\U0001f50d Filter options:", reply_markup=filter_menu_keyboard()
    )


@router.callback_query(F.data == "filters")
async def cb_filters(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    try:
        await callback.message.edit_text(
            "\U0001f50d Filter options:", reply_markup=filter_menu_keyboard()
        )
    except Exception:
        await callback.message.answer(
            "\U0001f50d Filter options:", reply_markup=filter_menu_keyboard()
        )


# ── Date filter ──────────────────────────────────────────────────────


@router.callback_query(F.data == "filter:date")
async def cb_filter_date(callback: types.CallbackQuery):
    await callback.answer()
    try:
        await callback.message.edit_text(
            "\U0001f4c5 Select date filter:", reply_markup=date_filter_keyboard()
        )
    except Exception:
        await callback.message.answer(
            "\U0001f4c5 Select date filter:", reply_markup=date_filter_keyboard()
        )


@router.callback_query(F.data.startswith("df:"))
async def cb_date_filter_choice(callback: types.CallbackQuery):
    await callback.answer()
    filter_type = callback.data.split(":")[1]
    resp = await backend.handle(
        {"action": "add_filter", "data": {"filter_type": filter_type}}
    )
    msg = resp.get("message", "Done")
    try:
        await callback.message.edit_text(msg, reply_markup=filter_menu_keyboard())
    except Exception:
        await callback.message.answer(msg, reply_markup=filter_menu_keyboard())


# ── Type filter ──────────────────────────────────────────────────────


@router.callback_query(F.data == "filter:type")
async def cb_filter_type(callback: types.CallbackQuery):
    await callback.answer()
    try:
        await callback.message.edit_text(
            "\U0001f4cb Select type filter:", reply_markup=type_filter_keyboard()
        )
    except Exception:
        await callback.message.answer(
            "\U0001f4cb Select type filter:", reply_markup=type_filter_keyboard()
        )


@router.callback_query(F.data.startswith("tf:"))
async def cb_type_filter_choice(callback: types.CallbackQuery):
    await callback.answer()
    filter_type = callback.data.split(":")[1]
    resp = await backend.handle(
        {"action": "add_filter", "data": {"filter_type": filter_type}}
    )
    msg = resp.get("message", "Done")
    try:
        await callback.message.edit_text(msg, reply_markup=filter_menu_keyboard())
    except Exception:
        await callback.message.answer(msg, reply_markup=filter_menu_keyboard())


# ── Amount filter ────────────────────────────────────────────────────


@router.callback_query(F.data == "filter:amount")
async def cb_filter_amount(callback: types.CallbackQuery):
    await callback.answer()
    try:
        await callback.message.edit_text(
            "\U0001f4b0 Select amount filter:", reply_markup=amount_filter_keyboard()
        )
    except Exception:
        await callback.message.answer(
            "\U0001f4b0 Select amount filter:", reply_markup=amount_filter_keyboard()
        )


@router.callback_query(F.data.startswith("af:"))
async def cb_amount_filter_choice(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    filter_type = callback.data.split(":")[1]

    if filter_type in ("custom_large", "custom_small"):
        await state.update_data(amount_filter_kind=filter_type)
        await state.set_state(FilterInput.amount_threshold)
        cancel_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Cancel", callback_data="filters")]
            ]
        )
        try:
            await callback.message.edit_text(
                "\U0001f4b0 Enter the amount threshold:", reply_markup=cancel_kb
            )
        except Exception:
            await callback.message.answer(
                "\U0001f4b0 Enter the amount threshold:", reply_markup=cancel_kb
            )
        return

    resp = await backend.handle(
        {"action": "add_filter", "data": {"filter_type": filter_type}}
    )
    msg = resp.get("message", "Done")
    try:
        await callback.message.edit_text(msg, reply_markup=filter_menu_keyboard())
    except Exception:
        await callback.message.answer(msg, reply_markup=filter_menu_keyboard())


@router.message(FilterInput.amount_threshold)
async def on_amount_threshold(message: types.Message, state: FSMContext):
    text = message.text.strip() if message.text else ""
    try:
        threshold = float(text)
        if threshold < 0:
            raise ValueError
    except ValueError:
        await message.answer("\u274c Please enter a valid positive number.")
        return

    data = await state.get_data()
    kind = data.get("amount_filter_kind", "custom_large")
    await state.clear()

    if kind == "custom_large":
        filter_type = "large_transactions"
    else:
        filter_type = "small_transactions"

    resp = await backend.handle(
        {
            "action": "add_filter",
            "data": {"filter_type": filter_type, "threshold": threshold},
        }
    )
    msg = resp.get("message", "Done")
    await message.answer(msg, reply_markup=filter_menu_keyboard())


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

    rows = []
    for i in range(0, len(all_cats), 2):
        row = [
            InlineKeyboardButton(text=c, callback_data=f"catf:{c}")
            for c in all_cats[i : i + 2]
        ]
        rows.append(row)
    rows.append([InlineKeyboardButton(text="Cancel", callback_data="filters")])
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    try:
        await callback.message.edit_text(
            "\U0001f3f7\ufe0f Select category to filter by (include only):",
            reply_markup=kb,
        )
    except Exception:
        await callback.message.answer(
            "\U0001f3f7\ufe0f Select category to filter by (include only):",
            reply_markup=kb,
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
    try:
        await callback.message.edit_text(msg, reply_markup=filter_menu_keyboard())
    except Exception:
        await callback.message.answer(msg, reply_markup=filter_menu_keyboard())


# ── Description filter ───────────────────────────────────────────────


@router.callback_query(F.data == "filter:description")
async def cb_filter_description(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(FilterInput.description_search)
    cancel_kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Cancel", callback_data="filters")]]
    )
    try:
        await callback.message.edit_text(
            "\U0001f4dd Send the search text to filter descriptions by:",
            reply_markup=cancel_kb,
        )
    except Exception:
        await callback.message.answer(
            "\U0001f4dd Send the search text to filter descriptions by:",
            reply_markup=cancel_kb,
        )


@router.message(FilterInput.description_search)
async def on_description_search(message: types.Message, state: FSMContext):
    text = message.text.strip() if message.text else ""
    if not text:
        await message.answer("\u274c Please enter a non-empty search term.")
        return

    await state.clear()
    resp = await backend.handle(
        {
            "action": "add_filter",
            "data": {"filter_type": "description", "search_term": text},
        }
    )
    msg = resp.get("message", "Done")
    await message.answer(msg, reply_markup=filter_menu_keyboard())


# ── View active / Clear all ──────────────────────────────────────────


@router.callback_query(F.data == "filter:view_active")
async def cb_view_active_filters(callback: types.CallbackQuery):
    await callback.answer()
    resp = await backend.handle({"action": "get_active_filters", "data": {}})
    if resp["status"] == "error":
        await callback.message.answer(resp["message"], reply_markup=back_to_menu(2))
        return
    text = fmt_filters(resp["data"]["filters"])
    try:
        await callback.message.edit_text(
            text, parse_mode="MarkdownV2", reply_markup=filter_menu_keyboard()
        )
    except Exception:
        await callback.message.answer(
            text, parse_mode="MarkdownV2", reply_markup=filter_menu_keyboard()
        )


@router.callback_query(F.data == "filter:clear_all")
async def cb_clear_all_filters(callback: types.CallbackQuery):
    await callback.answer()
    resp = await backend.handle({"action": "clear_filters", "data": {}})
    msg = resp.get("message", "Done")
    try:
        await callback.message.edit_text(
            msg, parse_mode="MarkdownV2", reply_markup=filter_menu_keyboard()
        )
    except Exception:
        await callback.message.answer(
            msg, parse_mode="MarkdownV2", reply_markup=filter_menu_keyboard()
        )
