"""Chart category visibility toggle handler."""

from aiogram import F, Router, types
from languages import t
from telegram.backend import backend, get_lang
from telegram.keyboards import chart_categories_keyboard, back_to_menu, parse_menu_page

router = Router()


async def _get_chart_data() -> tuple[dict, dict, str | None]:
    """Fetch categories from dashboard and hidden settings.

    Returns (categories_dict, hidden_dict, error_message).
    """
    dash_resp = await backend.handle({"action": "get_dashboard", "data": {}})
    if dash_resp.get("status") == "error":
        return {}, {}, dash_resp.get("message", "Error")

    dash_data = dash_resp.get("data", {})
    expense_cats = list((dash_data.get("expense_by_category") or {}).keys())
    income_cats = list((dash_data.get("income_by_category") or {}).keys())
    categories = {"expense": expense_cats, "income": income_cats}

    hidden_resp = await backend.handle(
        {"action": "get_hidden_chart_categories", "data": {}}
    )
    hidden = hidden_resp.get("data", {})
    if not isinstance(hidden, dict):
        hidden = {}

    return categories, hidden, None


@router.callback_query(F.data.startswith("chart_categories"))
async def cb_chart_categories(callback: types.CallbackQuery):
    await callback.answer()
    page = parse_menu_page(callback.data)
    lang = get_lang()

    categories, hidden, err = await _get_chart_data()
    if err:
        try:
            await callback.message.edit_text(err, reply_markup=back_to_menu(page))
        except Exception:
            await callback.message.answer(err, reply_markup=back_to_menu(page))
        return

    if not categories.get("expense") and not categories.get("income"):
        msg = t("chart_categories.no_data", lang)
        try:
            await callback.message.edit_text(msg, reply_markup=back_to_menu(page))
        except Exception:
            await callback.message.answer(msg, reply_markup=back_to_menu(page))
        return

    text = f"\U0001f4ca {t('chart_categories.select', lang)}"
    kb = chart_categories_keyboard(categories, hidden, page)
    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception:
        await callback.message.answer(text, reply_markup=kb)


@router.callback_query(F.data.startswith("chtog:"))
async def cb_toggle_category(callback: types.CallbackQuery):
    await callback.answer()
    # Format: chtog:{type}:{category}@{page}
    raw = callback.data.split(":", 1)[1]  # "expense:Food@1"
    page = parse_menu_page(raw)
    without_page = raw.rsplit("@", 1)[0]  # "expense:Food"
    cat_type, category = without_page.split(":", 1)

    # Get current hidden state
    hidden_resp = await backend.handle(
        {"action": "get_hidden_chart_categories", "data": {}}
    )
    hidden = hidden_resp.get("data", {})
    if not isinstance(hidden, dict):
        hidden = {}

    current_list = list(hidden.get(cat_type, []))
    if category in current_list:
        current_list.remove(category)
    else:
        current_list.append(category)

    hidden[cat_type] = current_list
    await backend.handle({"action": "set_hidden_chart_categories", "data": hidden})

    # Re-render the keyboard
    categories, hidden, err = await _get_chart_data()
    if err:
        try:
            await callback.message.edit_text(err, reply_markup=back_to_menu(page))
        except Exception:
            await callback.message.answer(err, reply_markup=back_to_menu(page))
        return

    lang = get_lang()
    text = f"\U0001f4ca {t('chart_categories.select', lang)}"
    kb = chart_categories_keyboard(categories, hidden, page)
    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception:
        pass  # Message unchanged — ignore


@router.callback_query(F.data == "noop")
async def cb_noop(callback: types.CallbackQuery):
    await callback.answer()
