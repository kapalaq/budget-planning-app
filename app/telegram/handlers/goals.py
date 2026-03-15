"""Savings goal handlers."""

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from languages import t
from telegram.backend import backend, get_lang
from telegram.keyboards import (
    back_to_menu,
    cancel_keyboard,
    goal_actions_keyboard,
    goal_list_keyboard,
    goal_menu_keyboard,
    skip_keyboard,
    frequency_keyboard,
    end_condition_keyboard,
)
from telegram.states import AddGoal, RecurringGoalSave, SaveToGoal
from telegram.utils import fmt_goal_detail, fmt_goals

router = Router()


# ── Goal menu ────────────────────────────────────────────────────────


@router.callback_query(F.data == "goals_menu")
async def cb_goals_menu(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        "\U0001f3af " + t("goal.tg_title", get_lang()),
        reply_markup=goal_menu_keyboard(),
    )


# ── List goals ───────────────────────────────────────────────────────


@router.callback_query(F.data.startswith("goals:"))
async def cb_goals_list(callback: types.CallbackQuery):
    await callback.answer()
    filter_type = callback.data.split(":", 1)[1]
    resp = await backend.handle(
        {"action": "get_goals", "data": {"filter": filter_type}}
    )
    if resp["status"] == "error":
        await callback.message.edit_text(resp["message"], reply_markup=back_to_menu(3))
        return
    goals = resp["data"]["goals"]
    label = filter_type.capitalize()
    text = fmt_goals(goals, label, lang=get_lang())
    await callback.message.edit_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=goal_list_keyboard(goals),
    )


# ── Goal detail ──────────────────────────────────────────────────────


@router.callback_query(F.data.startswith("gdet:"))
async def cb_goal_detail(callback: types.CallbackQuery):
    await callback.answer()
    name = callback.data.split(":", 1)[1]
    resp = await backend.handle({"action": "get_goal_detail", "data": {"name": name}})
    if resp["status"] == "error":
        await callback.message.edit_text(resp["message"], reply_markup=back_to_menu(3))
        return
    data = resp["data"]
    status = data.get("goal", {}).get("status", "active")
    text = fmt_goal_detail(data, lang=get_lang())
    await callback.message.edit_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=goal_actions_keyboard(name, status),
    )


# ── Add goal ─────────────────────────────────────────────────────────


@router.callback_query(F.data == "add_goal_start")
async def cb_add_goal_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await state.set_state(AddGoal.name)
    await callback.message.edit_text(
        "\U0001f3af " + t("goal.tg_enter_name", get_lang()),
        reply_markup=cancel_keyboard(3),
    )


@router.message(AddGoal.name)
async def add_goal_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    if not name:
        await message.answer("\u26a0\ufe0f " + t("wallet.tg_name_empty", get_lang()))
        return
    await state.update_data(name=name)
    await state.set_state(AddGoal.target)
    await message.answer(
        "\U0001f4b0 " + t("goal.tg_enter_target", get_lang()),
        reply_markup=cancel_keyboard(3),
    )


@router.message(AddGoal.target)
async def add_goal_target(message: types.Message, state: FSMContext):
    try:
        target = float(message.text.strip().replace(",", "."))
        if target <= 0:
            raise ValueError
    except (ValueError, AttributeError):
        await message.answer(
            "\u26a0\ufe0f " + t("transaction.tg_positive_number", get_lang())
        )
        return
    await state.update_data(target=target)
    await state.set_state(AddGoal.currency)
    await message.answer(
        "\U0001f4b1 " + t("goal.tg_enter_currency", get_lang()),
        reply_markup=skip_keyboard(3),
    )


@router.callback_query(AddGoal.currency, F.data == "skip_default")
async def add_goal_skip_currency(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(currency="KZT")
    await state.set_state(AddGoal.description)
    await callback.message.edit_text(
        "\U0001f4dd " + t("goal.tg_enter_description", get_lang()),
        reply_markup=skip_keyboard(3),
    )


@router.message(AddGoal.currency)
async def add_goal_currency(message: types.Message, state: FSMContext):
    text = message.text.strip()
    currency = "KZT" if text == "-" or text.lower() == "skip" else text.upper()
    await state.update_data(currency=currency)
    await state.set_state(AddGoal.description)
    await message.answer(
        "\U0001f4dd " + t("goal.tg_enter_description", get_lang()),
        reply_markup=skip_keyboard(3),
    )


@router.callback_query(AddGoal.description, F.data == "skip_default")
async def add_goal_skip_desc(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(description="")
    await _finish_add_goal(callback.message, state)


@router.message(AddGoal.description)
async def add_goal_description(message: types.Message, state: FSMContext):
    desc = message.text.strip()
    if desc == "-" or desc.lower() == "skip":
        desc = ""
    await state.update_data(description=desc)
    await _finish_add_goal(message, state)


async def _finish_add_goal(message: types.Message, state: FSMContext):
    data = await state.get_data()
    form = {
        "name": data["name"],
        "target": data["target"],
        "currency": data.get("currency", "KZT"),
        "goal_description": data.get("description") or data["name"],
    }
    resp = await backend.handle({"action": "add_goal", "data": form})
    await state.clear()
    msg = resp.get("message", "Done")
    await message.answer(msg, reply_markup=back_to_menu(3))


# ── Save to goal ─────────────────────────────────────────────────────


@router.callback_query(F.data.startswith("gsave:"))
async def cb_save_to_goal(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    name = callback.data.split(":", 1)[1]
    await state.clear()
    await state.update_data(goal_name=name)
    await state.set_state(SaveToGoal.amount)
    await callback.message.edit_text(
        "\U0001f4b0 " + t("goal.tg_save_amount", get_lang(), name=name),
        reply_markup=cancel_keyboard(3),
    )


@router.message(SaveToGoal.amount)
async def save_to_goal_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip().replace(",", "."))
        if amount <= 0:
            raise ValueError
    except (ValueError, AttributeError):
        await message.answer(
            "\u26a0\ufe0f " + t("transaction.tg_positive_number", get_lang())
        )
        return
    data = await state.get_data()
    goal_name = data["goal_name"]
    resp = await backend.handle(
        {
            "action": "save_to_goal",
            "data": {
                "goal_name": goal_name,
                "amount": amount,
                "description": f"Saving to {goal_name}",
            },
        }
    )
    await state.clear()
    msg = resp.get("message", "Done")
    await message.answer(msg, reply_markup=back_to_menu(3))


# ── Complete goal ────────────────────────────────────────────────────


@router.callback_query(F.data.startswith("gcomplete:"))
async def cb_complete_goal(callback: types.CallbackQuery):
    await callback.answer()
    name = callback.data.split(":", 1)[1]
    resp = await backend.handle({"action": "complete_goal", "data": {"name": name}})
    msg = resp.get("message", "Done")
    await callback.message.edit_text(msg, reply_markup=back_to_menu(3))


# ── Hide goal ────────────────────────────────────────────────────────


@router.callback_query(F.data.startswith("ghide:"))
async def cb_hide_goal(callback: types.CallbackQuery):
    await callback.answer()
    name = callback.data.split(":", 1)[1]
    resp = await backend.handle({"action": "hide_goal", "data": {"name": name}})
    msg = resp.get("message", "Done")
    await callback.message.edit_text(msg, reply_markup=back_to_menu(3))


# ── Reactivate goal ──────────────────────────────────────────────────


@router.callback_query(F.data.startswith("greactivate:"))
async def cb_reactivate_goal(callback: types.CallbackQuery):
    await callback.answer()
    name = callback.data.split(":", 1)[1]
    resp = await backend.handle({"action": "reactivate_goal", "data": {"name": name}})
    msg = resp.get("message", "Done")
    await callback.message.edit_text(msg, reply_markup=back_to_menu(3))


# ── Recurring save to goal ──────────────────────────────────────────


@router.callback_query(F.data.startswith("grecsave:"))
async def cb_recurring_goal_save(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    name = callback.data.split(":", 1)[1]
    await state.clear()
    await state.update_data(goal_name=name)
    await state.set_state(RecurringGoalSave.amount)
    await callback.message.edit_text(
        "\U0001f504 " + t("goal.tg_recurring_save_to", get_lang(), name=name),
        reply_markup=cancel_keyboard(3),
    )


@router.message(RecurringGoalSave.amount)
async def rec_goal_save_amount(message: types.Message, state: FSMContext):
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
    await state.set_state(RecurringGoalSave.description)
    await message.answer(
        "\U0001f4dd " + t("goal.tg_enter_description", get_lang()),
        reply_markup=skip_keyboard(3),
    )


@router.callback_query(RecurringGoalSave.description, F.data == "skip_default")
async def rec_goal_save_skip_desc(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(description="")
    await state.set_state(RecurringGoalSave.start_date)
    await callback.message.edit_text(
        "\U0001f4c5 " + t("goal.tg_enter_start_date", get_lang()),
        reply_markup=skip_keyboard(3),
    )


@router.message(RecurringGoalSave.description)
async def rec_goal_save_description(message: types.Message, state: FSMContext):
    desc = message.text.strip()
    if desc == "-" or desc.lower() == "skip":
        desc = ""
    await state.update_data(description=desc)
    await state.set_state(RecurringGoalSave.start_date)
    await message.answer(
        "\U0001f4c5 " + t("goal.tg_enter_start_date", get_lang()),
        reply_markup=skip_keyboard(3),
    )


@router.callback_query(RecurringGoalSave.start_date, F.data == "skip_default")
async def rec_goal_save_skip_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(start_date=None)
    await state.set_state(RecurringGoalSave.frequency)
    await callback.message.edit_text(
        "\U0001f504 " + t("recurring.tg_select_frequency", get_lang()),
        reply_markup=frequency_keyboard(3),
    )


@router.message(RecurringGoalSave.start_date)
async def rec_goal_save_start_date(message: types.Message, state: FSMContext):
    text = message.text.strip()
    date_val = None if text == "-" or text.lower() == "skip" else text
    await state.update_data(start_date=date_val)
    await state.set_state(RecurringGoalSave.frequency)
    await message.answer(
        "\U0001f504 " + t("recurring.tg_select_frequency", get_lang()),
        reply_markup=frequency_keyboard(3),
    )


@router.callback_query(RecurringGoalSave.frequency, F.data.startswith("freq:"))
async def rec_goal_save_frequency(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    freq = callback.data.split(":")[1]
    await state.update_data(frequency=freq)
    await state.set_state(RecurringGoalSave.interval)
    await callback.message.edit_text(
        t("transfer.tg_enter_interval", get_lang(), freq=freq),
        reply_markup=skip_keyboard(3),
    )


@router.callback_query(RecurringGoalSave.interval, F.data == "skip_default")
async def rec_goal_save_skip_interval(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(interval=1)
    await state.set_state(RecurringGoalSave.end_condition)
    await callback.message.edit_text(
        "\U0001f3c1 " + t("recurring.tg_select_end", get_lang()),
        reply_markup=end_condition_keyboard(3),
    )


@router.message(RecurringGoalSave.interval)
async def rec_goal_save_interval(message: types.Message, state: FSMContext):
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
    await state.set_state(RecurringGoalSave.end_condition)
    await message.answer(
        "\U0001f3c1 " + t("recurring.tg_select_end", get_lang()),
        reply_markup=end_condition_keyboard(3),
    )


@router.callback_query(RecurringGoalSave.end_condition, F.data.startswith("endc:"))
async def rec_goal_save_end_condition(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    endc = callback.data.split(":")[1]
    await state.update_data(end_condition=endc)
    if endc == "never":
        await _finish_recurring_goal_save(callback.message, state)
    elif endc == "on_date":
        await state.set_state(RecurringGoalSave.end_date)
        await callback.message.edit_text(
            "\U0001f4c5 " + t("recurring.tg_enter_end_date", get_lang()),
            reply_markup=cancel_keyboard(3),
        )
    elif endc == "after_count":
        await state.set_state(RecurringGoalSave.end_count)
        await callback.message.edit_text(
            "\U0001f522 " + t("recurring.tg_enter_count", get_lang()),
            reply_markup=cancel_keyboard(3),
        )


@router.message(RecurringGoalSave.end_date)
async def rec_goal_save_end_date(message: types.Message, state: FSMContext):
    await state.update_data(end_date=message.text.strip())
    await _finish_recurring_goal_save(message, state)


@router.message(RecurringGoalSave.end_count)
async def rec_goal_save_end_count(message: types.Message, state: FSMContext):
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
    await _finish_recurring_goal_save(message, state)


async def _finish_recurring_goal_save(message: types.Message, state: FSMContext):
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
        "goal_name": data["goal_name"],
        "amount": data["amount"],
        "description": data.get("description", ""),
        "start_date": data.get("start_date"),
        "recurrence_rule": rule,
    }
    resp = await backend.handle({"action": "add_recurring_goal_save", "data": form})
    await state.clear()
    msg = resp.get("message", "Done")
    await message.answer(msg, reply_markup=back_to_menu(3))
