"""FSM states for multi-step Telegram flows."""

from aiogram.fsm.state import State, StatesGroup


class AddTransaction(StatesGroup):
    amount = State()
    category = State()
    new_category = State()
    description = State()
    date = State()


class Transfer(StatesGroup):
    target_wallet = State()
    amount = State()
    description = State()
    date = State()


class AddWallet(StatesGroup):
    wallet_type = State()
    name = State()
    currency = State()
    starting_value = State()
    description = State()
    interest_rate = State()
    term_months = State()
    capitalization = State()


class EditTransaction(StatesGroup):
    field_select = State()
    amount = State()
    category = State()
    new_category = State()
    description = State()
    date = State()


class EditWallet(StatesGroup):
    field_select = State()
    new_name = State()
    currency = State()
    description = State()


class AddRecurring(StatesGroup):
    amount = State()
    category = State()
    new_category = State()
    description = State()
    start_date = State()
    frequency = State()
    interval = State()
    end_condition = State()
    end_date = State()
    end_count = State()


class DeleteRecurring(StatesGroup):
    delete_option = State()
