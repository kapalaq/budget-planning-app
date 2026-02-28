"""Reusable inline keyboards for the Telegram bot."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="+ Income", callback_data="add_income"),
                InlineKeyboardButton(text="- Expense", callback_data="add_expense"),
            ],
            [
                InlineKeyboardButton(text="Transfer", callback_data="transfer"),
                InlineKeyboardButton(text="Percentages", callback_data="percentages"),
            ],
            [
                InlineKeyboardButton(text="Wallets", callback_data="wallets"),
                InlineKeyboardButton(text="Add Wallet", callback_data="add_wallet"),
            ],
            [
                InlineKeyboardButton(text="Recurring", callback_data="recurring_list"),
                InlineKeyboardButton(text="Sorting", callback_data="sorting"),
            ],
            [
                InlineKeyboardButton(
                    text="+ Recurring Income", callback_data="add_recurring_income"
                ),
                InlineKeyboardButton(
                    text="- Recurring Expense", callback_data="add_recurring_expense"
                ),
            ],
            [
                InlineKeyboardButton(text="Filters", callback_data="filters"),
                InlineKeyboardButton(text="Help", callback_data="help"),
            ],
            [
                InlineKeyboardButton(text="Refresh", callback_data="dashboard"),
            ],
        ]
    )


def back_to_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="<< Menu", callback_data="dashboard")]
        ]
    )


def cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Cancel", callback_data="cancel")]]
    )


def confirm_keyboard(action: str, payload: str = "") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Yes", callback_data=f"confirm_{action}:{payload}"
                ),
                InlineKeyboardButton(text="No", callback_data="dashboard"),
            ]
        ]
    )


def category_keyboard(
    categories: list[str], add_new: bool = True
) -> InlineKeyboardMarkup:
    rows = []
    for i in range(0, len(categories), 2):
        row = [
            InlineKeyboardButton(text=c, callback_data=f"cat:{c}")
            for c in categories[i : i + 2]
        ]
        rows.append(row)
    if add_new:
        rows.append(
            [InlineKeyboardButton(text="+ New Category", callback_data="cat:__new__")]
        )
    rows.append([InlineKeyboardButton(text="Cancel", callback_data="cancel")])
    return rows_to_markup(rows)


def wallet_type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Regular", callback_data="wtype:regular"),
                InlineKeyboardButton(text="Deposit", callback_data="wtype:deposit"),
            ],
            [InlineKeyboardButton(text="Cancel", callback_data="cancel")],
        ]
    )


def wallet_list_keyboard(
    wallets: list[dict], action_prefix: str = "sw"
) -> InlineKeyboardMarkup:
    rows = []
    for w in wallets:
        name = w["name"]
        label = f"{w['name']} ({w['currency']}) {w['balance']:.2f}"
        rows.append(
            [InlineKeyboardButton(text=label, callback_data=f"{action_prefix}:{name}")]
        )
    rows.append([InlineKeyboardButton(text="<< Menu", callback_data="dashboard")])
    return rows_to_markup(rows)


def sorting_keyboard(options: dict[str, str]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=name, callback_data=f"sort:{key}")]
        for key, name in options.items()
    ]
    rows.append([InlineKeyboardButton(text="<< Menu", callback_data="dashboard")])
    return rows_to_markup(rows)


def filter_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="By Date", callback_data="filter:date"),
                InlineKeyboardButton(text="By Type", callback_data="filter:type"),
            ],
            [
                InlineKeyboardButton(
                    text="By Category", callback_data="filter:category"
                ),
                InlineKeyboardButton(text="By Amount", callback_data="filter:amount"),
            ],
            [
                InlineKeyboardButton(
                    text="By Description", callback_data="filter:description"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="View Active", callback_data="filter:view_active"
                ),
                InlineKeyboardButton(
                    text="Clear All", callback_data="filter:clear_all"
                ),
            ],
            [InlineKeyboardButton(text="<< Menu", callback_data="dashboard")],
        ]
    )


def date_filter_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Today", callback_data="df:today"),
                InlineKeyboardButton(text="Last Week", callback_data="df:last_week"),
            ],
            [
                InlineKeyboardButton(text="Last Month", callback_data="df:last_month"),
                InlineKeyboardButton(text="This Month", callback_data="df:this_month"),
            ],
            [
                InlineKeyboardButton(text="Last Year", callback_data="df:last_year"),
                InlineKeyboardButton(text="This Year", callback_data="df:this_year"),
            ],
            [InlineKeyboardButton(text="Cancel", callback_data="filters")],
        ]
    )


def type_filter_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Income Only", callback_data="tf:income"),
                InlineKeyboardButton(text="Expense Only", callback_data="tf:expense"),
            ],
            [
                InlineKeyboardButton(
                    text="Transfers Only", callback_data="tf:transfers_only"
                ),
                InlineKeyboardButton(
                    text="No Transfers", callback_data="tf:no_transfers"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Recurring Only", callback_data="tf:recurring_only"
                ),
                InlineKeyboardButton(
                    text="Non-Recurring", callback_data="tf:non_recurring"
                ),
            ],
            [InlineKeyboardButton(text="Cancel", callback_data="filters")],
        ]
    )


def amount_filter_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Large (>10000)", callback_data="af:large_transactions"
                ),
                InlineKeyboardButton(
                    text="Small (<100)", callback_data="af:small_transactions"
                ),
            ],
            [InlineKeyboardButton(text="Cancel", callback_data="filters")],
        ]
    )


def transaction_actions_keyboard(index: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Edit", callback_data=f"edit_tx:{index}"),
                InlineKeyboardButton(text="Delete", callback_data=f"del_tx:{index}"),
            ],
            [InlineKeyboardButton(text="<< Menu", callback_data="dashboard")],
        ]
    )


def recurring_actions_keyboard(index: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Edit", callback_data=f"edit_rec:{index}"),
                InlineKeyboardButton(text="Delete", callback_data=f"del_rec:{index}"),
            ],
            [InlineKeyboardButton(text="<< Menu", callback_data="dashboard")],
        ]
    )


def wallet_actions_keyboard(name: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Switch to", callback_data=f"sw:{name}"),
                InlineKeyboardButton(text="Edit", callback_data=f"edit_w:{name}"),
            ],
            [
                InlineKeyboardButton(text="Delete", callback_data=f"del_w:{name}"),
                InlineKeyboardButton(text="<< Menu", callback_data="dashboard"),
            ],
        ]
    )


def delete_recurring_keyboard(index: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Template Only", callback_data=f"delrec_opt:{index}:1"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Template + Future",
                    callback_data=f"delrec_opt:{index}:2",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Template + All",
                    callback_data=f"delrec_opt:{index}:3",
                ),
            ],
            [InlineKeyboardButton(text="Cancel", callback_data="dashboard")],
        ]
    )


def frequency_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Daily", callback_data="freq:daily"),
                InlineKeyboardButton(text="Weekly", callback_data="freq:weekly"),
            ],
            [
                InlineKeyboardButton(text="Monthly", callback_data="freq:monthly"),
                InlineKeyboardButton(text="Yearly", callback_data="freq:yearly"),
            ],
            [InlineKeyboardButton(text="Cancel", callback_data="cancel")],
        ]
    )


def end_condition_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Never", callback_data="endc:never")],
            [
                InlineKeyboardButton(
                    text="On Specific Date", callback_data="endc:on_date"
                )
            ],
            [
                InlineKeyboardButton(
                    text="After N Occurrences", callback_data="endc:after_count"
                )
            ],
            [InlineKeyboardButton(text="Cancel", callback_data="cancel")],
        ]
    )


def capitalization_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Yes", callback_data="cap:yes"),
                InlineKeyboardButton(text="No", callback_data="cap:no"),
            ],
        ]
    )


def edit_transaction_fields_keyboard(
    index: int, is_transfer: bool = False
) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="Amount", callback_data=f"etf:{index}:amount")],
    ]
    if not is_transfer:
        rows.append(
            [
                InlineKeyboardButton(
                    text="Category", callback_data=f"etf:{index}:category"
                )
            ]
        )
    rows.extend(
        [
            [
                InlineKeyboardButton(
                    text="Description", callback_data=f"etf:{index}:description"
                )
            ],
            [InlineKeyboardButton(text="Date", callback_data=f"etf:{index}:date")],
            [
                InlineKeyboardButton(text="Save", callback_data=f"etf:{index}:save"),
                InlineKeyboardButton(text="Cancel", callback_data="dashboard"),
            ],
        ]
    )
    return rows_to_markup(rows)


def edit_wallet_fields_keyboard(name: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Name", callback_data=f"ewf:{name}:name"),
                InlineKeyboardButton(
                    text="Currency", callback_data=f"ewf:{name}:currency"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Description", callback_data=f"ewf:{name}:description"
                ),
            ],
            [
                InlineKeyboardButton(text="Save", callback_data=f"ewf:{name}:save"),
                InlineKeyboardButton(text="Cancel", callback_data="dashboard"),
            ],
        ]
    )


def edit_recurring_keyboard(index: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Edit Template", callback_data=f"erec:{index}:template"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Skip a Date", callback_data=f"erec:{index}:skip"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Toggle Active/Paused",
                    callback_data=f"erec:{index}:toggle",
                ),
            ],
            [InlineKeyboardButton(text="Cancel", callback_data="dashboard")],
        ]
    )


def rows_to_markup(rows: list[list[InlineKeyboardButton]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=rows)
