"""Timezone selection handler."""

from aiogram import F, Router, types
from languages import t
from telegram.backend import backend, get_lang
from telegram.keyboards import back_to_menu, parse_menu_page, timezone_keyboard

router = Router()


@router.callback_query(F.data.startswith("timezone"))
async def cb_timezone(callback: types.CallbackQuery):
    await callback.answer()
    page = parse_menu_page(callback.data)
    lang = get_lang()
    resp = await backend.handle({"action": "get_timezone", "data": {}})
    current = resp.get("data", {}).get("timezone", 0)
    try:
        await callback.message.edit_text(
            f"\U0001f552 {t('timezone.select', lang)}",
            reply_markup=timezone_keyboard(current, page),
        )
    except Exception:
        await callback.message.answer(
            f"\U0001f552 {t('timezone.select', lang)}",
            reply_markup=timezone_keyboard(current, page),
        )


@router.callback_query(F.data.startswith("tzpage:"))
async def cb_timezone_page(callback: types.CallbackQuery):
    await callback.answer()
    # Format: tzpage:{tz_page}@{menu_page}
    parts = callback.data.split(":", 1)[1]
    menu_page = parse_menu_page(parts)
    tz_page = int(parts.split("@")[0])
    lang = get_lang()
    resp = await backend.handle({"action": "get_timezone", "data": {}})
    current = resp.get("data", {}).get("timezone", 0)
    try:
        await callback.message.edit_text(
            f"\U0001f552 {t('timezone.select', lang)}",
            reply_markup=timezone_keyboard(current, menu_page, tz_page),
        )
    except Exception:
        await callback.message.answer(
            f"\U0001f552 {t('timezone.select', lang)}",
            reply_markup=timezone_keyboard(current, menu_page, tz_page),
        )


@router.callback_query(F.data.startswith("settz:"))
async def cb_set_timezone(callback: types.CallbackQuery):
    await callback.answer()
    page = parse_menu_page(callback.data)
    # Format: settz:{offset}@{page}
    offset_str = callback.data.split(":", 1)[1].split("@")[0]
    offset = int(offset_str)
    resp = await backend.handle(
        {"action": "set_timezone", "data": {"timezone": offset}}
    )
    if callback.from_user:
        backend.set_cached_timezone(callback.from_user.id, offset)
    msg = resp.get("message", t("common.done", get_lang()))
    try:
        await callback.message.edit_text(msg, reply_markup=back_to_menu(page))
    except Exception:
        await callback.message.answer(msg, reply_markup=back_to_menu(page))
