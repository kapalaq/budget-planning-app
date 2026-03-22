"""Help handler."""

from aiogram import F, Router, types
from aiogram.filters import Command
from languages import t
from telegram.backend import get_lang
from telegram.keyboards import back_to_menu, parse_menu_page
from telegram.utils import _bold, _italic, _to_md2

router = Router()


def _build_help_text(lang: str) -> str:
    _HELP_PLAIN = (
        f"\U0001f4b0 {_bold(t('help.tg_title', lang))}\n\n"
        f"\U0001f4b5 {_bold(t('help.tg_transaction_cmds', lang))}\n"
        f"{_italic(t('help.tg_use_menu', lang))}\n"
        f"\U0001f4cb {_bold(t('btn.transactions', lang))} - {t('help.tg_transactions_desc', lang)}\n"
        f"\U0001f504 {_bold(t('btn.recurring', lang))} - {t('help.tg_recurring_desc', lang)}\n"
        f"{t('help.tg_edit_delete_hint', lang)}\n"
        f"\U0001f522 {_bold(t('btn.sort', lang))} - {t('help.tg_sort_desc', lang)}\n"
        f"\U0001f50d {_bold(t('btn.filters', lang))} - {t('help.tg_filters_desc', lang)}\n"
        f"{t('help.tg_wallet_scope', lang)}\n\n"
        f"\u2699\ufe0f {_bold(t('help.tg_functional_cmds', lang))}\n"
        f"{_italic(t('help.tg_use_menu', lang))}\n"
        f"\U0001f4b5 {_bold(t('btn.income', lang))} - {t('help.tg_income_desc', lang)}\n"
        f"\U0001f4b8 {_bold(t('btn.expense', lang))} - {t('help.tg_expense_desc', lang)}\n"
        f"\U0001f4b5\U0001f504 {_bold(t('btn.rec_income', lang))} - {t('help.tg_rec_income_desc', lang)}\n"
        f"\U0001f4b8\U0001f504 {_bold(t('btn.rec_expense', lang))} - {t('help.tg_rec_expense_desc', lang)}\n"
        f"{t('help.tg_rec_note', lang)}\n\n"
        f"\U0001f45b {_bold(t('help.tg_wallet_cmds', lang))}\n"
        f"{_italic(t('help.tg_use_menu', lang))}\n"
        f"\U0001f45b {_bold(t('btn.wallets', lang))} - {t('help.tg_wallets_desc', lang)}\n"
        f"{t('help.tg_wallet_edit_hint', lang)}\n"
        f"\U0001f522 {_bold(t('btn.sort', lang))} - {t('help.tg_wallet_sort_desc', lang)}\n"
        f"\u2795 {_bold(t('btn.add_wallet', lang))} - {t('help.tg_add_wallet_desc', lang)}\n"
        f"\U0001f500 {_bold(t('btn.transfer', lang))} - {t('help.tg_transfer_desc', lang)}\n"
        f"\U0001f4ca {_bold(t('btn.percentages', lang))} - {t('help.tg_percentages_desc', lang)}\n\n"
        f"\u2328\ufe0f {_bold(t('help.tg_bottom', lang))}\n"
        f"\U0001f504 {_bold(t('common.refresh', lang))} - {t('help.tg_refresh_desc', lang)}\n"
        f"{_bold(t('btn.disconnect', lang))} - {t('help.tg_logout_desc', lang)}"
    )
    return _to_md2(_HELP_PLAIN)


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = _build_help_text(get_lang())
    await message.answer(
        help_text, parse_mode="MarkdownV2", reply_markup=back_to_menu()
    )


@router.callback_query(F.data.startswith("help"))
async def cb_help(callback: types.CallbackQuery):
    await callback.answer()
    page = parse_menu_page(callback.data)
    help_text = _build_help_text(get_lang())
    try:
        await callback.message.edit_text(
            help_text, parse_mode="MarkdownV2", reply_markup=back_to_menu(page)
        )
    except Exception:
        await callback.message.answer(
            help_text, parse_mode="MarkdownV2", reply_markup=back_to_menu(page)
        )
