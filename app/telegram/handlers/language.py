"""Language selection handler."""

from aiogram import F, Router, types
from languages import t
from telegram.backend import backend, get_lang
from telegram.keyboards import back_to_menu, language_keyboard, parse_menu_page

router = Router()


@router.callback_query(F.data.startswith("language"))
async def cb_language(callback: types.CallbackQuery):
    await callback.answer()
    page = parse_menu_page(callback.data)
    lang = get_lang()
    resp = await backend.handle({"action": "get_language", "data": {}})
    current = resp.get("data", {}).get("language", "en-US")
    try:
        await callback.message.edit_text(
            f"\U0001f310 {t('language.select', lang)}",
            reply_markup=language_keyboard(current),
        )
    except Exception:
        await callback.message.answer(
            f"\U0001f310 {t('language.select', lang)}",
            reply_markup=language_keyboard(current),
        )


@router.callback_query(F.data.startswith("setlang:"))
async def cb_set_language(callback: types.CallbackQuery):
    await callback.answer()
    lang = callback.data.split(":", 1)[1]
    resp = await backend.handle({"action": "set_language", "data": {"language": lang}})
    # Update the cached language
    if callback.from_user:
        backend.set_cached_language(callback.from_user.id, lang)
    msg = resp.get("message", t("common.done", lang))
    try:
        await callback.message.edit_text(msg, reply_markup=back_to_menu())
    except Exception:
        await callback.message.answer(msg, reply_markup=back_to_menu())
