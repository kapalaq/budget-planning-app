"""Help handler."""

from aiogram import Router, types
from aiogram.filters import Command

from telegram.keyboards import back_to_menu
from telegram.utils import _bold, _italic, _code, _to_md2

router = Router()

_HELP_PLAIN = (
    f"\U0001f4b0 {_bold('Budget Planner Bot')}\n\n"
    ""
    f"\U0001f4b5 {_bold('Transaction Commands:')}\n"
    f"{_italic('(Use the menu buttons)')}\n"
    f"\U0001f4cb {_bold('Transactions')} - Show all transactions.\n"
    f"\U0001f504 {_bold('Recurring')} - Show all recurring transactions.\n"
    "By choosing any transaction from both lists "
    "you can edit/delete it.\n"
    f"\U0001f522 {_bold('Sort')} - A sorting config for transactions' list.\n"
    f"\U0001f50d {_bold('Filters')} - A filtering config for transactions' list\n"
    "Both will be activated only for a current wallet.\n\n"
    ""
    f"\u2699\ufe0f {_bold('Functional Commands:')}\n"
    f"{_italic('(Use the menu buttons)')}\n"
    f"\U0001f4b5 {_bold('+ Income')} - Add income\n"
    f"\U0001f4b8 {_bold('- Expense')} - Add expense\n"
    f"\U0001f4b5\U0001f504 {_bold('+ Rec Income')} - Add recurrent income\n"
    f"\U0001f4b8\U0001f504 {_bold('- Rec Expense')} - Add recurrent expense\n"
    "Note: Recurrent Operations will produce transactions with configured "
    "periodicity starting from the start date. It means if your recurrent "
    "transaction was set up to start in 2000 and produce yearly expense, "
    "then you will have 26 expenses, starting in 2000 and lasting in the "
    "current year.\n\n"
    ""
    f"\U0001f45b {_bold('Wallet Commands:')}\n"
    f"{_italic('(Use the menu buttons)')}\n"
    f"\U0001f45b {_bold('Wallets')} - List wallets\n"
    "By choosing any wallet from the list "
    "you can edit/delete it.\n"
    f"\U0001f522 {_bold('Sort')} - A sorting config for wallets' list.\n"
    f"\u2795 {_bold('Add Wallet')} - Create wallet\n"
    f"\U0001f500 {_bold('Transfer')} - Make a transfer from current wallet "
    "to any other wallet you possess.\n"
    f"\U0001f4ca {_bold('Percentages')} - Shows income/outcome "
    "proportional (%) breakdown by categories.\n\n"
    f"\u2328\ufe0f {_bold('Bottom buttons:')}\n"
    f"\U0001f504 {_bold('Refresh')} - Refresh dashboard (main page)\n"
    f"{_bold('Logout')} - Log out from your current session."
)

HELP_TEXT = _to_md2(_HELP_PLAIN)


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        HELP_TEXT, parse_mode="MarkdownV2", reply_markup=back_to_menu()
    )


@router.callback_query(lambda c: c.data == "help")
async def cb_help(callback: types.CallbackQuery):
    await callback.answer()
    try:
        await callback.message.edit_text(
            HELP_TEXT, parse_mode="MarkdownV2", reply_markup=back_to_menu()
        )
    except Exception:
        await callback.message.answer(
            HELP_TEXT, parse_mode="MarkdownV2", reply_markup=back_to_menu()
        )
