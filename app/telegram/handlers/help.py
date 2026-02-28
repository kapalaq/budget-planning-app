"""Help handler."""

from aiogram import Router, types
from aiogram.filters import Command

from telegram.keyboards import back_to_menu
from telegram.utils import _bold, _code, _to_md2

router = Router()

_HELP_PLAIN = (
    f"{_bold('Budget Planner Bot')}\n\n"
    f"{_bold('Transaction Commands:')}\n"
    "Use the menu buttons or:\n"
    "/income - Add income\n"
    "/expense - Add expense\n"
    "/transfer - Transfer between wallets\n"
    "/percentages - Category breakdown\n\n"
    f"{_bold('Wallet Commands:')}\n"
    "/wallets - List wallets\n"
    "/add_wallet - Create wallet\n\n"
    f"{_bold('Recurring:')}\n"
    "/recurring - List recurring transactions\n\n"
    f"{_bold('Other:')}\n"
    "/dashboard - Show dashboard\n"
    "/sorting - Change sorting\n"
    "/filters - Manage filters\n"
    "/help - This message\n\n"
    f"{_bold('Inline actions:')}\n"
    f"Use {_code('show N')}, {_code('edit N')}, {_code('delete N')} "
    "to manage transactions by index.\n"
    f"Use {_code('wallet NAME')}, {_code('switch NAME')} "
    "for wallet operations."
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
