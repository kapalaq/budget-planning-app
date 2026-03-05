"""Reusable inline keyboards for the Telegram bot."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu(page: int = 1) -> InlineKeyboardMarkup:
    if page == 1:
        rows = [
            [
                InlineKeyboardButton(
                    text="\U0001f4cb Transactions",
                    callback_data="tx_list_show",
                ),
                InlineKeyboardButton(
                    text="\U0001f504 Recurring",
                    callback_data="recurring_list",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="\U0001f522 Sort",
                    callback_data="sorting",
                ),
                InlineKeyboardButton(
                    text="\U0001f50d Filters", callback_data="filters"
                ),
            ],
            [
                InlineKeyboardButton(text="\u2753 Help", callback_data="help"),
            ],
            [
                InlineKeyboardButton(text="Next >>", callback_data="menu_page:2"),
            ],
            [
                InlineKeyboardButton(
                    text="\U0001f504 Refresh", callback_data="menu_page:1"
                ),
                InlineKeyboardButton(text="Disconnect", callback_data="disconnect"),
            ],
        ]
    elif page == 2:
        rows = [
            [
                InlineKeyboardButton(
                    text="\U0001f4b5 + Income", callback_data="add_income"
                ),
                InlineKeyboardButton(
                    text="\U0001f4b8 - Expense", callback_data="add_expense"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="\U0001f4b5\U0001f504 + Rec Income",
                    callback_data="add_recurring_income",
                ),
                InlineKeyboardButton(
                    text="\U0001f4b8\U0001f504 - Rec Expense",
                    callback_data="add_recurring_expense",
                ),
            ],
            [
                InlineKeyboardButton(text="\u2753 Help", callback_data="help"),
            ],
            [
                InlineKeyboardButton(text="<< Prev", callback_data="menu_page:1"),
                InlineKeyboardButton(text="Next >>", callback_data="menu_page:3"),
            ],
            [
                InlineKeyboardButton(
                    text="\U0001f504 Refresh", callback_data="menu_page:2"
                ),
                InlineKeyboardButton(text="Disconnect", callback_data="disconnect"),
            ],
        ]
    else:  # page == 3
        rows = [
            [
                InlineKeyboardButton(
                    text="\U0001f45b Wallets", callback_data="wallets"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="\U0001f522 Sort",
                    callback_data="wallet_sorting",
                ),
                InlineKeyboardButton(
                    text="\u2795 Add Wallet", callback_data="add_wallet"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="\U0001f500 Transfer", callback_data="transfer"
                ),
                InlineKeyboardButton(
                    text="\U0001f4ca Percentages", callback_data="percentages"
                ),
            ],
            [
                InlineKeyboardButton(text="<< Prev", callback_data="menu_page:2"),
            ],
            [
                InlineKeyboardButton(
                    text="\U0001f504 Refresh", callback_data="menu_page:3"
                ),
                InlineKeyboardButton(text="Disconnect", callback_data="disconnect"),
            ],
        ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def transaction_list_keyboard(
    transactions: list[dict], action_prefix: str, page: int = 0, page_size: int = 5
) -> InlineKeyboardMarkup:
    start = page * page_size
    end = start + page_size
    page_items = transactions[start:end]
    rows = []
    for i, t in enumerate(page_items, start + 1):
        label = f"{i}. {t['display']}"
        if len(label) > 60:
            label = label[:57] + "..."
        rows.append(
            [InlineKeyboardButton(text=label, callback_data=f"{action_prefix}:{i}")]
        )
    nav = []
    if page > 0:
        nav.append(
            InlineKeyboardButton(
                text="<< Prev", callback_data=f"txpage:{action_prefix}:{page - 1}"
            )
        )
    if end < len(transactions):
        nav.append(
            InlineKeyboardButton(
                text="Next >>", callback_data=f"txpage:{action_prefix}:{page + 1}"
            )
        )
    if nav:
        rows.append(nav)
    rows.append(
        [InlineKeyboardButton(text="\u2b05\ufe0f Menu", callback_data="menu_page:1")]
    )
    return rows_to_markup(rows)


def back_to_menu(page: int = 1) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="\u2b05\ufe0f Menu", callback_data=f"menu_page:{page}"
                )
            ]
        ]
    )


def cancel_keyboard(page: int = 1) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="\u274c Cancel", callback_data=f"menu_page:{page}"
                )
            ]
        ]
    )


def confirm_keyboard(
    action: str, payload: str = "", page: int = 1
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="\u2705 Yes", callback_data=f"confirm_{action}:{payload}"
                ),
                InlineKeyboardButton(
                    text="\u274c No", callback_data=f"menu_page:{page}"
                ),
            ]
        ]
    )


def category_keyboard(
    categories: list[str], add_new: bool = True, page: int = 1
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
            [
                InlineKeyboardButton(
                    text="\u2795 New Category", callback_data="cat:__new__"
                )
            ]
        )
    rows.append(
        [InlineKeyboardButton(text="\u274c Cancel", callback_data=f"menu_page:{page}")]
    )
    return rows_to_markup(rows)


def wallet_type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="\U0001f45b Regular", callback_data="wtype:regular"
                ),
                InlineKeyboardButton(
                    text="\U0001f3e6 Deposit", callback_data="wtype:deposit"
                ),
            ],
            [InlineKeyboardButton(text="\u274c Cancel", callback_data="wallets")],
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
    rows.append(
        [InlineKeyboardButton(text="\u2b05\ufe0f Menu", callback_data="menu_page:3")]
    )
    return rows_to_markup(rows)


def sorting_keyboard(options: dict[str, str]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=name, callback_data=f"sort:{key}")]
        for key, name in options.items()
    ]
    rows.append(
        [InlineKeyboardButton(text="\u2b05\ufe0f Menu", callback_data="menu_page:1")]
    )
    return rows_to_markup(rows)


def filter_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="\U0001f4c5 By Date", callback_data="filter:date"
                ),
                InlineKeyboardButton(
                    text="\U0001f4cb By Type", callback_data="filter:type"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="\U0001f3f7\ufe0f By Category", callback_data="filter:category"
                ),
                InlineKeyboardButton(
                    text="\U0001f4b0 By Amount", callback_data="filter:amount"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="\U0001f4dd By Description", callback_data="filter:description"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="\U0001f441\ufe0f View Active",
                    callback_data="filter:view_active",
                ),
                InlineKeyboardButton(
                    text="\U0001f9f9 Clear All", callback_data="filter:clear_all"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="\u2b05\ufe0f Menu", callback_data="menu_page:1"
                )
            ],
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
            [InlineKeyboardButton(text="\u274c Cancel", callback_data="filters")],
        ]
    )


def type_filter_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Income Only", callback_data="tf:income_only"
                ),
                InlineKeyboardButton(
                    text="Expense Only", callback_data="tf:expense_only"
                ),
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
            [InlineKeyboardButton(text="\u274c Cancel", callback_data="filters")],
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
            [
                InlineKeyboardButton(
                    text="Custom Large (>=)", callback_data="af:custom_large"
                ),
                InlineKeyboardButton(
                    text="Custom Small (<=)", callback_data="af:custom_small"
                ),
            ],
            [InlineKeyboardButton(text="\u274c Cancel", callback_data="filters")],
        ]
    )


def transaction_actions_keyboard(index: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="\u270f\ufe0f Edit", callback_data=f"edit_tx:{index}"
                ),
                InlineKeyboardButton(
                    text="\U0001f5d1\ufe0f Delete", callback_data=f"del_tx:{index}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="\u2b05\ufe0f Menu", callback_data="menu_page:1"
                )
            ],
        ]
    )


def recurring_actions_keyboard(index: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="\u270f\ufe0f Edit", callback_data=f"edit_rec:{index}"
                ),
                InlineKeyboardButton(
                    text="\U0001f5d1\ufe0f Delete", callback_data=f"del_rec:{index}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="\u2b05\ufe0f Menu", callback_data="menu_page:1"
                )
            ],
        ]
    )


def wallet_actions_keyboard(name: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="\U0001f500 Switch to", callback_data=f"sw:{name}"
                ),
                InlineKeyboardButton(
                    text="\u270f\ufe0f Edit", callback_data=f"edit_w:{name}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="\U0001f5d1\ufe0f Delete", callback_data=f"del_w:{name}"
                ),
                InlineKeyboardButton(
                    text="\u2b05\ufe0f Menu", callback_data="menu_page:3"
                ),
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
            [InlineKeyboardButton(text="\u274c Cancel", callback_data="menu_page:1")],
        ]
    )


def frequency_keyboard(page: int = 1) -> InlineKeyboardMarkup:
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
            [
                InlineKeyboardButton(
                    text="\u274c Cancel", callback_data=f"menu_page:{page}"
                )
            ],
        ]
    )


def end_condition_keyboard(page: int = 1) -> InlineKeyboardMarkup:
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
            [
                InlineKeyboardButton(
                    text="\u274c Cancel", callback_data=f"menu_page:{page}"
                )
            ],
        ]
    )


def capitalization_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="\u2705 Yes", callback_data="cap:yes"),
                InlineKeyboardButton(text="\u274c No", callback_data="cap:no"),
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
                InlineKeyboardButton(
                    text="\U0001f4be Save", callback_data=f"etf:{index}:save"
                ),
                InlineKeyboardButton(text="\u274c Cancel", callback_data="menu_page:1"),
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
                InlineKeyboardButton(
                    text="\U0001f4be Save", callback_data=f"ewf:{name}:save"
                ),
                InlineKeyboardButton(text="\u274c Cancel", callback_data="menu_page:3"),
            ],
        ]
    )


def edit_recurring_keyboard(index: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="\u270f\ufe0f Edit Template",
                    callback_data=f"erec:{index}:template",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="\u23e9 Skip a Date", callback_data=f"erec:{index}:skip"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="\u23ef\ufe0f Toggle Active/Paused",
                    callback_data=f"erec:{index}:toggle",
                ),
            ],
            [InlineKeyboardButton(text="\u274c Cancel", callback_data="menu_page:1")],
        ]
    )


def rows_to_markup(rows: list[list[InlineKeyboardButton]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=rows)
