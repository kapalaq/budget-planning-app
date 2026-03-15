"""Transfer handler."""

from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from languages import t
from telegram.backend import backend, get_lang
from telegram.keyboards import (
    cancel_keyboard,
    skip_keyboard,
    back_to_menu,
    wallet_list_keyboard,
    frequency_keyboard,
    end_condition_keyboard,
)
from telegram.states import Transfer, RecurringTransfer

router = Router()


@router.message(Command("transfer"))
async def cmd_transfer(message: types.Message, state: FSMContext):
    await _start_transfer(message, state)


@router.callback_query(F.data == "transfer")
async def cb_transfer(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await _start_transfer(callback.message, state)


async def _start_transfer(message: types.Message, state: FSMContext):
    await state.clear()
    resp = await backend.handle({"action": "get_transfer_context", "data": {}})
    if resp["status"] == "error":
        try:
            await message.edit_text(resp["message"], reply_markup=back_to_menu(3))
        except Exception:
            await message.answer(resp["message"], reply_markup=back_to_menu(3))
        return
    from_wallet = resp["data"]["from_wallet"]
    targets = resp["data"]["target_wallets"]
    if not targets:
        try:
            await message.edit_text(
                "\u26a0\ufe0f " + t("transfer.tg_no_targets", get_lang()),
                reply_markup=back_to_menu(3),
            )
        except Exception:
            await message.answer(
                "\u26a0\ufe0f " + t("transfer.tg_no_targets", get_lang()),
                reply_markup=back_to_menu(3),
            )
        return
    await state.update_data(from_wallet=from_wallet, targets=targets)
    await state.set_state(Transfer.target_wallet)
    try:
        await message.edit_text(
            "\U0001f500 "
            + t(
                "transfer.tg_from",
                get_lang(),
                name=from_wallet["name"],
                balance=f"{from_wallet['balance']:.2f}",
            ),
            reply_markup=wallet_list_keyboard(targets, action_prefix="xfer_to"),
        )
    except Exception:
        await message.answer(
            "\U0001f500 "
            + t(
                "transfer.tg_from",
                get_lang(),
                name=from_wallet["name"],
                balance=f"{from_wallet['balance']:.2f}",
            ),
            reply_markup=wallet_list_keyboard(targets, action_prefix="xfer_to"),
        )


@router.callback_query(Transfer.target_wallet, F.data.startswith("xfer_to:"))
async def transfer_target(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    target_name = callback.data.split(":", 1)[1]
    await state.update_data(target_wallet_name=target_name)
    await state.set_state(Transfer.amount)
    try:
        await callback.message.edit_text(
            "\U0001f3af " + t("transfer.tg_target", get_lang(), name=target_name),
            reply_markup=cancel_keyboard(3),
        )
    except Exception:
        await callback.message.answer(
            "\U0001f3af " + t("transfer.tg_target", get_lang(), name=target_name),
            reply_markup=cancel_keyboard(3),
        )


@router.message(Transfer.amount)
async def transfer_amount(message: types.Message, state: FSMContext):
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
    await state.set_state(Transfer.description)
    await message.answer(
        "\U0001f4dd " + t("transfer.tg_enter_description", get_lang()),
        reply_markup=skip_keyboard(3),
    )


@router.callback_query(Transfer.description, F.data == "skip_default")
async def transfer_skip_description(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(description="")
    await state.set_state(Transfer.date)
    await callback.message.edit_text(
        "\U0001f4c5 " + t("transfer.tg_enter_date", get_lang()),
        reply_markup=skip_keyboard(3),
    )


@router.message(Transfer.description)
async def transfer_description(message: types.Message, state: FSMContext):
    desc = message.text.strip()
    if desc == "-" or desc.lower() == "skip":
        desc = ""
    await state.update_data(description=desc)
    await state.set_state(Transfer.date)
    await message.answer(
        "\U0001f4c5 " + t("transfer.tg_enter_date", get_lang()),
        reply_markup=skip_keyboard(3),
    )


@router.callback_query(Transfer.date, F.data == "skip_default")
async def transfer_skip_date(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    form = {
        "target_wallet_name": data["target_wallet_name"],
        "amount": data["amount"],
        "description": data.get("description", ""),
        "date": None,
    }
    resp = await backend.handle({"action": "transfer", "data": form})
    await state.clear()
    msg = resp.get("message", "Done")
    await callback.message.edit_text(msg, reply_markup=back_to_menu(3))


@router.message(Transfer.date)
async def transfer_date(message: types.Message, state: FSMContext):
    text = message.text.strip()
    date_val = None if text == "-" or text.lower() == "skip" else text
    data = await state.get_data()
    form = {
        "target_wallet_name": data["target_wallet_name"],
        "amount": data["amount"],
        "description": data.get("description", ""),
        "date": date_val,
    }
    resp = await backend.handle({"action": "transfer", "data": form})
    await state.clear()
    msg = resp.get("message", "Done")
    try:
        await message.edit_text(msg, reply_markup=back_to_menu(3))
    except Exception:
        await message.answer(msg, reply_markup=back_to_menu(3))


# ── Recurring Transfer ──────────────────────────────────────────────


@router.callback_query(F.data == "recurring_transfer")
async def cb_recurring_transfer(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    resp = await backend.handle({"action": "get_transfer_context", "data": {}})
    if resp["status"] == "error":
        await callback.message.edit_text(resp["message"], reply_markup=back_to_menu(3))
        return
    targets = resp["data"]["target_wallets"]
    from_wallet = resp["data"]["from_wallet"]
    if not targets:
        await callback.message.edit_text(
            "\u26a0\ufe0f No target wallets available.",
            reply_markup=back_to_menu(3),
        )
        return
    await state.update_data(from_wallet=from_wallet, targets=targets)
    await state.set_state(RecurringTransfer.target_wallet)
    await callback.message.edit_text(
        "\U0001f504 "
        + t("transfer.tg_recurring_from", get_lang(), name=from_wallet["name"]),
        reply_markup=wallet_list_keyboard(targets, action_prefix="rxfer_to"),
    )


@router.callback_query(RecurringTransfer.target_wallet, F.data.startswith("rxfer_to:"))
async def rec_transfer_target(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    target_name = callback.data.split(":", 1)[1]
    await state.update_data(target_wallet_name=target_name)
    await state.set_state(RecurringTransfer.amount)
    await callback.message.edit_text(
        f"\U0001f3af Target: {target_name}\n\U0001f4b2 Enter amount:",
        reply_markup=cancel_keyboard(3),
    )


@router.message(RecurringTransfer.amount)
async def rec_transfer_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip().replace(",", "."))
        if amount <= 0:
            raise ValueError
    except (ValueError, AttributeError):
        await message.answer(
            "\u26a0\ufe0f " + t("transaction.tg_positive_number", get_lang())
        )
        return
    await state.update_data(amount=amount)
    await state.set_state(RecurringTransfer.description)
    await message.answer(
        "\U0001f4dd " + t("transfer.tg_enter_description", get_lang()),
        reply_markup=skip_keyboard(3),
    )


@router.callback_query(RecurringTransfer.description, F.data == "skip_default")
async def rec_transfer_skip_desc(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(description="")
    await state.set_state(RecurringTransfer.start_date)
    await callback.message.edit_text(
        "\U0001f4c5 " + t("recurring.tg_enter_start_date", get_lang()),
        reply_markup=skip_keyboard(3),
    )


@router.message(RecurringTransfer.description)
async def rec_transfer_description(message: types.Message, state: FSMContext):
    desc = message.text.strip()
    if desc == "-" or desc.lower() == "skip":
        desc = ""
    await state.update_data(description=desc)
    await state.set_state(RecurringTransfer.start_date)
    await message.answer(
        "\U0001f4c5 " + t("recurring.tg_enter_start_date", get_lang()),
        reply_markup=skip_keyboard(3),
    )


@router.callback_query(RecurringTransfer.start_date, F.data == "skip_default")
async def rec_transfer_skip_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(start_date=None)
    await state.set_state(RecurringTransfer.frequency)
    await callback.message.edit_text(
        "\U0001f504 " + t("recurring.tg_select_frequency", get_lang()),
        reply_markup=frequency_keyboard(3),
    )


@router.message(RecurringTransfer.start_date)
async def rec_transfer_start_date(message: types.Message, state: FSMContext):
    text = message.text.strip()
    date_val = None if text == "-" or text.lower() == "skip" else text
    await state.update_data(start_date=date_val)
    await state.set_state(RecurringTransfer.frequency)
    await message.answer(
        "\U0001f504 " + t("recurring.tg_select_frequency", get_lang()),
        reply_markup=frequency_keyboard(3),
    )


@router.callback_query(RecurringTransfer.frequency, F.data.startswith("freq:"))
async def rec_transfer_frequency(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    freq = callback.data.split(":")[1]
    await state.update_data(frequency=freq)
    await state.set_state(RecurringTransfer.interval)
    await callback.message.edit_text(
        t("transfer.tg_enter_interval", get_lang(), freq=freq),
        reply_markup=skip_keyboard(3),
    )


@router.callback_query(RecurringTransfer.interval, F.data == "skip_default")
async def rec_transfer_skip_interval(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(interval=1)
    await state.set_state(RecurringTransfer.end_condition)
    await callback.message.edit_text(
        "\U0001f3c1 " + t("recurring.tg_select_end", get_lang()),
        reply_markup=end_condition_keyboard(3),
    )


@router.message(RecurringTransfer.interval)
async def rec_transfer_interval(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if text == "-" or text.lower() == "skip":
        interval = 1
    else:
        try:
            interval = int(text)
            if interval <= 0:
                raise ValueError
        except ValueError:
            await message.answer(
                "\u26a0\ufe0f " + t("recurring.tg_positive_integer", get_lang())
            )
            return
    await state.update_data(interval=interval)
    await state.set_state(RecurringTransfer.end_condition)
    await message.answer(
        "\U0001f3c1 " + t("recurring.tg_select_end", get_lang()),
        reply_markup=end_condition_keyboard(3),
    )


@router.callback_query(RecurringTransfer.end_condition, F.data.startswith("endc:"))
async def rec_transfer_end_condition(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    endc = callback.data.split(":")[1]
    await state.update_data(end_condition=endc)
    if endc == "never":
        await _finish_recurring_transfer(callback.message, state)
    elif endc == "on_date":
        await state.set_state(RecurringTransfer.end_date)
        await callback.message.edit_text(
            "\U0001f4c5 " + t("recurring.tg_enter_end_date", get_lang()),
            reply_markup=cancel_keyboard(3),
        )
    elif endc == "after_count":
        await state.set_state(RecurringTransfer.end_count)
        await callback.message.edit_text(
            "\U0001f522 " + t("recurring.tg_enter_count", get_lang()),
            reply_markup=cancel_keyboard(3),
        )


@router.message(RecurringTransfer.end_date)
async def rec_transfer_end_date(message: types.Message, state: FSMContext):
    await state.update_data(end_date=message.text.strip())
    await _finish_recurring_transfer(message, state)


@router.message(RecurringTransfer.end_count)
async def rec_transfer_end_count(message: types.Message, state: FSMContext):
    try:
        count = int(message.text.strip())
        if count <= 0:
            raise ValueError
    except (ValueError, AttributeError):
        await message.answer(
            "\u26a0\ufe0f " + t("recurring.tg_positive_integer", get_lang())
        )
        return
    await state.update_data(max_occurrences=count)
    await _finish_recurring_transfer(message, state)


async def _finish_recurring_transfer(message: types.Message, state: FSMContext):
    data = await state.get_data()
    rule = {
        "frequency": data["frequency"],
        "interval": data.get("interval", 1),
        "end_condition": data["end_condition"],
    }
    if data["end_condition"] == "on_date":
        rule["end_date"] = data["end_date"]
    elif data["end_condition"] == "after_count":
        rule["max_occurrences"] = data["max_occurrences"]

    form = {
        "target_wallet_name": data["target_wallet_name"],
        "amount": data["amount"],
        "description": data.get("description", ""),
        "start_date": data.get("start_date"),
        "recurrence_rule": rule,
    }
    resp = await backend.handle({"action": "add_recurring_transfer", "data": form})
    await state.clear()
    msg = resp.get("message", "Done")
    await message.answer(msg, reply_markup=back_to_menu(3))
