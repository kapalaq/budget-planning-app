"""Transaction handlers: add, show, edit, delete."""

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from languages import t
from telegram.backend import backend, get_lang
from telegram.keyboards import (
    category_keyboard,
    cancel_keyboard,
    skip_keyboard,
    back_to_menu,
    transaction_actions_keyboard,
    edit_transaction_fields_keyboard,
    confirm_keyboard,
    transaction_list_keyboard,
)
from telegram.states import AddTransaction, EditTransaction
from telegram.utils import fmt_transaction, _to_md2

router = Router()


# ── Add transaction ──────────────────────────────────────────────────


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
        await message.edit_text(resp["message"])
        return
    categories = resp["data"]["categories"]
    await state.update_data(transaction_type=tt, categories=categories)
    await state.set_state(AddTransaction.amount)
    lang = get_lang()
    label = (
        "\U0001f4b5 " + t("common.income", lang)
        if tt == "income"
        else "\U0001f4b8 " + t("common.expense", lang)
    )
    await message.edit_text(
        t("transaction.tg_adding", lang, label=label),
        reply_markup=cancel_keyboard(1),
    )


@router.message(AddTransaction.amount)
async def add_tx_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        if amount <= 0:
            raise ValueError
    except (ValueError, AttributeError):
        await message.answer(
            "\u26a0\ufe0f " + t("transaction.tg_positive_number", get_lang())
        )
        return
    await state.update_data(amount=amount)
    data = await state.get_data()
    await state.set_state(AddTransaction.category)
    await message.answer(
        "\U0001f3f7\ufe0f " + t("transaction.tg_select_category", get_lang()),
        reply_markup=category_keyboard(data["categories"], page=2),
    )


@router.callback_query(AddTransaction.category, F.data.startswith("cat:"))
async def add_tx_category(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    cat = callback.data.split(":", 1)[1]
    if cat == "__new__":
        await state.set_state(AddTransaction.new_category)
        await callback.message.edit_text(
            "\u2795 " + t("transaction.tg_new_category", get_lang()),
            reply_markup=cancel_keyboard(1),
        )
        return
    await state.update_data(category=cat)
    await state.set_state(AddTransaction.description)
    await callback.message.edit_text(
        "\U0001f4dd " + t("transaction.tg_enter_description", get_lang()),
        reply_markup=skip_keyboard(2),
    )


@router.message(AddTransaction.new_category)
async def add_tx_new_cat(message: types.Message, state: FSMContext):
    cat = message.text.strip()
    if not cat:
        await message.answer(
            "\u26a0\ufe0f " + t("transaction.tg_category_empty", get_lang())
        )
        return
    await state.update_data(category=cat)
    await state.set_state(AddTransaction.description)
    await message.answer(
        "\U0001f4dd " + t("transaction.tg_enter_description", get_lang()),
        reply_markup=skip_keyboard(2),
    )


@router.callback_query(AddTransaction.description, F.data == "skip_default")
async def add_tx_skip_description(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(description="")
    await state.set_state(AddTransaction.date)
    await callback.message.edit_text(
        "\U0001f4c5 " + t("transaction.tg_enter_date", get_lang()),
        reply_markup=skip_keyboard(2),
    )


@router.message(AddTransaction.description)
async def add_tx_description(message: types.Message, state: FSMContext):
    desc = message.text.strip()
    if desc == "-" or desc.lower() == "skip":
        desc = ""
    await state.update_data(description=desc)
    await state.set_state(AddTransaction.date)
    await message.answer(
        "\U0001f4c5 " + t("transaction.tg_enter_date", get_lang()),
        reply_markup=skip_keyboard(2),
    )


@router.callback_query(AddTransaction.date, F.data == "skip_default")
async def add_tx_skip_date(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    form = {
        "transaction_type": data["transaction_type"],
        "amount": data["amount"],
        "category": data["category"],
        "description": data.get("description", ""),
        "date": None,
    }
    resp = await backend.handle({"action": "add_transaction", "data": form})
    await state.clear()
    if resp["status"] == "success":
        await callback.message.edit_text(
            "\u2705 "
            + t(
                "transaction.tg_added",
                get_lang(),
                amount=f"{data['amount']:.2f}",
                category=data["category"],
            ),
            reply_markup=back_to_menu(2),
        )
    else:
        await callback.message.edit_text(resp["message"], reply_markup=back_to_menu(2))


@router.message(AddTransaction.date)
async def add_tx_date(message: types.Message, state: FSMContext):
    text = message.text.strip()
    date_val = None if text == "-" or text.lower() == "skip" else text
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
            "\u2705 "
            + t(
                "transaction.tg_added",
                get_lang(),
                amount=f"{data['amount']:.2f}",
                category=data["category"],
            ),
            reply_markup=back_to_menu(2),
        )
    else:
        await message.answer(resp["message"], reply_markup=back_to_menu(2))


# ── Transaction list pickers (from paginated menu) ───────────────────


async def _fetch_transactions():
    resp = await backend.handle({"action": "get_dashboard", "data": {}})
    if resp["status"] == "error":
        return None, resp["message"]
    return resp["data"].get("transactions", []), None


@router.callback_query(F.data == "tx_list_show")
async def cb_tx_list_show(callback: types.CallbackQuery):
    await callback.answer()
    transactions, err = await _fetch_transactions()
    if err:
        await callback.message.edit_text(err, reply_markup=back_to_menu(2))
        return
    if not transactions:
        await callback.message.edit_text(
            "\U0001f4ed " + t("transaction.tg_no_transactions", get_lang()),
            reply_markup=back_to_menu(2),
        )
        return
    await callback.message.edit_text(
        "\U0001f4cb " + t("transaction.tg_select_to_view", get_lang()),
        reply_markup=transaction_list_keyboard(transactions, "show_tx"),
    )


@router.callback_query(F.data.startswith("txpage:"))
async def cb_tx_page(callback: types.CallbackQuery):
    await callback.answer()
    parts = callback.data.split(":")
    action_prefix = parts[1]
    page = int(parts[2])
    transactions, err = await _fetch_transactions()
    if err:
        await callback.message.answer(err, reply_markup=back_to_menu(2))
        return
    try:
        await callback.message.edit_reply_markup(
            reply_markup=transaction_list_keyboard(transactions, action_prefix, page),
        )
    except Exception:
        pass


# ── Show transaction ─────────────────────────────────────────────────


@router.callback_query(F.data.startswith("show_tx:"))
async def cb_show_tx(callback: types.CallbackQuery):
    await callback.answer()
    index = int(callback.data.split(":")[1])
    await _show_transaction(callback.message, index)


async def _show_transaction(message: types.Message, index: int):
    resp = await backend.handle({"action": "get_transaction", "data": {"index": index}})
    if resp["status"] == "error":
        await message.edit_text(resp["message"], reply_markup=back_to_menu(2))
        return
    text = fmt_transaction(resp["data"], lang=get_lang())
    await message.edit_text(
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
        await callback.message.edit_text(resp["message"], reply_markup=back_to_menu())
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
    await callback.message.edit_text(
        "\u270f\ufe0f " + t("transaction.tg_editing", get_lang(), index=index),
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
            await callback.message.edit_text(
                "\u2139\ufe0f " + t("transaction.tg_no_changes", get_lang()),
                reply_markup=back_to_menu(),
            )
            await state.clear()
            return
        edit_data["index"] = index
        resp = await backend.handle({"action": "edit_transaction", "data": edit_data})
        await state.clear()
        msg = resp.get("message", "Done")
        await callback.message.edit_text(msg, reply_markup=back_to_menu())
        return

    if field == "amount":
        await state.set_state(EditTransaction.amount)
        await callback.message.edit_text(
            "\U0001f4b2 " + t("transaction.tg_enter_new_amount", get_lang()),
            reply_markup=cancel_keyboard(),
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
        await callback.message.edit_text(
            "\U0001f3f7\ufe0f " + t("transaction.tg_select_new_category", get_lang()),
            reply_markup=category_keyboard(cats),
        )
    elif field == "description":
        await state.set_state(EditTransaction.description)
        await callback.message.edit_text(
            "\U0001f4dd " + t("transaction.tg_enter_new_description", get_lang()),
            reply_markup=skip_keyboard(),
        )
    elif field == "date":
        await state.set_state(EditTransaction.date)
        await callback.message.edit_text(
            "\U0001f4c5 " + t("transaction.tg_enter_new_date", get_lang()),
            reply_markup=cancel_keyboard(),
        )


@router.message(EditTransaction.amount)
async def edit_tx_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        if amount <= 0:
            raise ValueError
    except (ValueError, AttributeError):
        await message.answer(
            "\u26a0\ufe0f " + t("transaction.tg_positive_number", get_lang())
        )
        return
    data = await state.get_data()
    edit_data = data.get("edit_data", {})
    edit_data["amount"] = amount
    index = data["edit_index"]
    current = data["current"]
    await state.update_data(edit_data=edit_data)
    await state.set_state(EditTransaction.field_select)
    await message.answer(
        "\u2705 "
        + t("transaction.tg_amount_updated", get_lang(), amount=f"{amount:.2f}"),
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
        await callback.message.edit_text(
            "\u2795 " + t("transaction.tg_new_category", get_lang()),
            reply_markup=cancel_keyboard(),
        )
        return
    data = await state.get_data()
    edit_data = data.get("edit_data", {})
    edit_data["category"] = cat
    index = data["edit_index"]
    current = data["current"]
    await state.update_data(edit_data=edit_data)
    await state.set_state(EditTransaction.field_select)
    await callback.message.edit_text(
        "\u2705 " + t("transaction.tg_category_updated", get_lang(), cat=cat),
        reply_markup=edit_transaction_fields_keyboard(
            index, current.get("is_transfer", False)
        ),
    )


@router.message(EditTransaction.new_category)
async def edit_tx_new_cat(message: types.Message, state: FSMContext):
    cat = message.text.strip()
    if not cat:
        await message.answer(
            "\u26a0\ufe0f " + t("transaction.tg_category_empty", get_lang())
        )
        return
    data = await state.get_data()
    edit_data = data.get("edit_data", {})
    edit_data["category"] = cat
    index = data["edit_index"]
    current = data["current"]
    await state.update_data(edit_data=edit_data)
    await state.set_state(EditTransaction.field_select)
    await message.answer(
        "\u2705 " + t("transaction.tg_category_set", get_lang(), cat=cat),
        reply_markup=edit_transaction_fields_keyboard(
            index, current.get("is_transfer", False)
        ),
    )


@router.callback_query(EditTransaction.description, F.data == "skip_default")
async def edit_tx_skip_description(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    edit_data = data.get("edit_data", {})
    edit_data["description"] = ""
    index = data["edit_index"]
    current = data["current"]
    await state.update_data(edit_data=edit_data)
    await state.set_state(EditTransaction.field_select)
    await callback.message.edit_text(
        "\u2705 " + t("transaction.tg_description_cleared", get_lang()),
        reply_markup=edit_transaction_fields_keyboard(
            index, current.get("is_transfer", False)
        ),
    )


@router.message(EditTransaction.description)
async def edit_tx_description(message: types.Message, state: FSMContext):
    desc = message.text.strip()
    if desc == "-" or desc.lower() == "skip":
        desc = ""
    data = await state.get_data()
    edit_data = data.get("edit_data", {})
    edit_data["description"] = desc
    index = data["edit_index"]
    current = data["current"]
    await state.update_data(edit_data=edit_data)
    await state.set_state(EditTransaction.field_select)
    await message.answer(
        "\u2705 " + t("transaction.tg_description_updated", get_lang()),
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
        "\u2705 " + t("transaction.tg_date_updated", get_lang(), date=date_val),
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
        await callback.message.edit_text(resp["message"], reply_markup=back_to_menu())
        return
    text = fmt_transaction(resp["data"], lang=get_lang())
    warning = ""
    if resp["data"].get("is_transfer"):
        warning = _to_md2(
            "\n\u26a0\ufe0f " + t("transaction.tg_transfer_delete_warning", get_lang())
        )
    suffix = _to_md2(
        "\n\U0001f5d1\ufe0f " + t("transaction.tg_confirm_delete", get_lang())
    )
    await callback.message.edit_text(
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
    await callback.message.edit_text(msg, reply_markup=back_to_menu())
