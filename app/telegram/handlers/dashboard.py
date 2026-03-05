"""Dashboard and start handlers."""

from aiogram import Router, F, types
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext

from telegram.backend import _current_token, backend
from telegram.keyboards import main_menu, back_to_menu
from telegram.utils import fmt_dashboard, _to_md2

router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext, command: CommandObject):
    await state.clear()

    # Handle deep link: /start <link_code>
    if command.args:
        code = command.args.strip()
        result = await backend.link_telegram(code, message.from_user.id)
        if result.get("status") == "error":
            await message.answer(
                "\u274c Invalid or expired link code.\n\n"
                "Generate a new link from the CLI app and try again."
            )
            return
        _current_token.set(result["token"])
        await message.answer("\u2705 Telegram account linked successfully!")
        await _show_dashboard_new(message)
        return

    # Check if this Telegram user has a linked account
    if message.from_user and message.from_user.id not in backend._tokens:
        token = await backend.ensure_auth(message.from_user.id)
        if not token:
            await message.answer(
                "\U0001f44b Welcome to Budget Planner!\n\n"
                "To get started, link your account from the CLI app:\n"
                "1. Login in the CLI\n"
                "2. Choose to link Telegram\n"
                "3. Tap the generated link"
            )
            return

    await _show_dashboard_new(message)


@router.message(Command("dashboard", "home", "menu"))
async def cmd_dashboard(message: types.Message, state: FSMContext):
    await state.clear()
    await _show_dashboard_new(message)


@router.callback_query(lambda c: c.data == "dashboard")
async def cb_dashboard(callback: types.CallbackQuery, state: FSMContext):
    """Legacy callback — redirect to menu_page:1 (dashboard)."""
    await state.clear()
    await callback.answer()
    await _show_dashboard_edit(callback.message)


@router.callback_query(F.data.startswith("menu_page:"))
async def cb_menu_page(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    page = int(callback.data.split(":")[1])

    await state.clear()
    await _show_dashboard_edit(callback.message, page)


async def _show_dashboard_edit(message: types.Message, page: int = 1):
    """Fetch dashboard data and edit the existing message."""
    resp = await backend.handle({"action": "process_recurring", "data": {}})
    count = resp.get("data", {}).get("generated_count", 0)

    resp = await backend.handle({"action": "get_dashboard", "data": {}})
    if resp["status"] == "error":
        try:
            await message.edit_text(resp["message"], reply_markup=back_to_menu(page))
        except Exception:
            pass
        return

    text = fmt_dashboard(resp["data"])
    if count > 0:
        prefix = _to_md2(f"\U0001f504 {count} recurring transaction(s) generated")
        text = f"{prefix}\n\n{text}"
    try:
        await message.edit_text(
            text, reply_markup=main_menu(page), parse_mode="MarkdownV2"
        )
    except Exception:
        pass


async def _show_dashboard_new(message: types.Message):
    """Fetch dashboard data and send as a new message."""
    resp = await backend.handle({"action": "process_recurring", "data": {}})
    count = resp.get("data", {}).get("generated_count", 0)

    resp = await backend.handle({"action": "get_dashboard", "data": {}})
    if resp["status"] == "error":
        await message.answer(resp["message"], reply_markup=back_to_menu())
        return

    text = fmt_dashboard(resp["data"])
    if count > 0:
        prefix = _to_md2(f"\U0001f504 {count} recurring transaction(s) generated")
        text = f"{prefix}\n\n{text}"

    await message.answer(text, reply_markup=main_menu(), parse_mode="MarkdownV2")
