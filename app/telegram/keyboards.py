"""Reusable inline keyboards for the Telegram bot."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from languages import t
from telegram.backend import get_lang


def parse_menu_page(data: str, default: int = 1) -> int:
    """Extract menu page number from callback data like 'action@2'.

    Returns *default* when the callback carries no ``@N`` suffix.
    """
    if "@" in data:
        try:
            return int(data.rsplit("@", 1)[1])
        except (ValueError, IndexError):
            pass
    return default


def main_menu(page: int = 1) -> InlineKeyboardMarkup:
    lang = get_lang()
    if page == 1:
        rows = [
            [
                InlineKeyboardButton(
                    text=f"\U0001f4b5 {t('btn.income', lang)}",
                    callback_data=f"add_income@{page}",
                ),
                InlineKeyboardButton(
                    text=f"\U0001f4b8 {t('btn.expense', lang)}",
                    callback_data=f"add_expense@{page}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"\U0001f4b5\U0001f504 {t('btn.rec_income', lang)}",
                    callback_data=f"add_recurring_income@{page}",
                ),
                InlineKeyboardButton(
                    text=f"\U0001f4b8\U0001f504 {t('btn.rec_expense', lang)}",
                    callback_data=f"add_recurring_expense@{page}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"\u2753 {t('btn.help', lang)}",
                    callback_data=f"help@{page}",
                ),
                InlineKeyboardButton(
                    text=f"\U0001f310 {t('language.title', lang)}",
                    callback_data=f"language@{page}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"\U0001f552 {t('timezone.title', lang)}",
                    callback_data=f"timezone@{page}",
                ),
                InlineKeyboardButton(
                    text=f"\U0001f4ca {t('btn.chart_categories', lang)}",
                    callback_data=f"chart_categories@{page}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t("common.next", lang), callback_data="menu_page:2"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"\U0001f504 {t('common.refresh', lang)}",
                    callback_data="menu_page:1",
                ),
                InlineKeyboardButton(
                    text=t("btn.disconnect", lang), callback_data="disconnect"
                ),
            ],
        ]
    elif page == 2:
        rows = [
            [
                InlineKeyboardButton(
                    text=f"\U0001f4cb {t('btn.transactions', lang)}",
                    callback_data=f"tx_list_show@{page}",
                ),
                InlineKeyboardButton(
                    text=f"\U0001f504 {t('btn.recurring', lang)}",
                    callback_data=f"recurring_list@{page}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"\U0001f522 {t('btn.sort', lang)}",
                    callback_data=f"sorting@{page}",
                ),
                InlineKeyboardButton(
                    text=f"\U0001f50d {t('btn.filters', lang)}",
                    callback_data=f"filters@{page}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"\U0001f4ca {t('btn.percentages', lang)}",
                    callback_data=f"percentages@{page}",
                ),
                InlineKeyboardButton(
                    text=f"\U0001f3af {t('btn.goals', lang)}",
                    callback_data=f"goals_menu@{page}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t("common.prev", lang), callback_data="menu_page:1"
                ),
                InlineKeyboardButton(
                    text=t("common.next", lang), callback_data="menu_page:3"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"\U0001f504 {t('common.refresh', lang)}",
                    callback_data="menu_page:2",
                ),
                InlineKeyboardButton(
                    text=t("btn.disconnect", lang), callback_data="disconnect"
                ),
            ],
        ]
    elif page == 3:
        rows = [
            [
                InlineKeyboardButton(
                    text=f"\U0001f45b {t('btn.wallets', lang)}",
                    callback_data=f"wallets@{page}",
                ),
                InlineKeyboardButton(
                    text=f"\U0001f4b1 {t('btn.portfolio', lang)}",
                    callback_data=f"portfolio@{page}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"\U0001f522 {t('btn.sort', lang)}",
                    callback_data=f"wallet_sorting@{page}",
                ),
                InlineKeyboardButton(
                    text=f"\u2795 {t('btn.add_wallet', lang)}",
                    callback_data=f"add_wallet@{page}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"\U0001f500 {t('btn.transfer', lang)}",
                    callback_data=f"transfer@{page}",
                ),
                InlineKeyboardButton(
                    text=f"\U0001f500\U0001f504 {t('btn.rec_transfer', lang)}",
                    callback_data=f"recurring_transfer@{page}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"\U0001f4cb {t('btn.bills', lang)}",
                    callback_data=f"bills_menu@{page}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t("common.prev", lang), callback_data="menu_page:2"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"\U0001f504 {t('common.refresh', lang)}",
                    callback_data="menu_page:3",
                ),
                InlineKeyboardButton(
                    text=t("btn.disconnect", lang), callback_data="disconnect"
                ),
            ],
        ]
    else:
        rows = [
            [
                InlineKeyboardButton(
                    text=f"\U0001f45b {t('btn.wallets', lang)}",
                    callback_data=f"wallets@{page}",
                ),
                InlineKeyboardButton(
                    text=f"\U0001f4b1 {t('btn.portfolio', lang)}",
                    callback_data=f"portfolio@{page}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"\U0001f522 {t('btn.sort', lang)}",
                    callback_data=f"wallet_sorting@{page}",
                ),
                InlineKeyboardButton(
                    text=f"\u2795 {t('btn.add_wallet', lang)}",
                    callback_data=f"add_wallet@{page}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"\U0001f500 {t('btn.transfer', lang)}",
                    callback_data=f"transfer@{page}",
                ),
                InlineKeyboardButton(
                    text=f"\U0001f500\U0001f504 {t('btn.rec_transfer', lang)}",
                    callback_data=f"recurring_transfer@{page}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"\U0001f4cb {t('btn.bills', lang)}",
                    callback_data=f"bills_menu@{page}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t("common.prev", lang), callback_data="menu_page:2"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"\U0001f504 {t('common.refresh', lang)}",
                    callback_data="menu_page:3",
                ),
                InlineKeyboardButton(
                    text=t("btn.disconnect", lang), callback_data="disconnect"
                ),
            ],
        ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def transaction_list_keyboard(
    transactions: list[dict],
    action_prefix: str,
    page: int = 0,
    page_size: int = 5,
    menu_page: int = 2,
) -> InlineKeyboardMarkup:
    lang = get_lang()
    start = page * page_size
    end = start + page_size
    page_items = transactions[start:end]
    rows = []
    for i, tr in enumerate(page_items, start + 1):
        label = f"{i}. {tr['display']}"
        if len(label) > 60:
            label = label[:57] + "..."
        rows.append(
            [InlineKeyboardButton(text=label, callback_data=f"{action_prefix}:{i}")]
        )
    nav = []
    if page > 0:
        nav.append(
            InlineKeyboardButton(
                text=f"<< {t('common.prev', lang)}",
                callback_data=f"txpage:{action_prefix}:{page - 1}:{menu_page}",
            )
        )
    if end < len(transactions):
        nav.append(
            InlineKeyboardButton(
                text=f"{t('common.next', lang)} >>",
                callback_data=f"txpage:{action_prefix}:{page + 1}:{menu_page}",
            )
        )
    if nav:
        rows.append(nav)
    rows.append(
        [
            InlineKeyboardButton(
                text=f"\u2b05\ufe0f {t('common.menu', lang)}",
                callback_data=f"menu_page:{menu_page}",
            )
        ]
    )
    return rows_to_markup(rows)


def back_to_menu(page: int = 1) -> InlineKeyboardMarkup:
    lang = get_lang()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"\u2b05\ufe0f {t('common.menu', lang)}",
                    callback_data=f"menu_page:{page}",
                )
            ]
        ]
    )


def cancel_keyboard(page: int = 1) -> InlineKeyboardMarkup:
    lang = get_lang()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"\u274c {t('common.cancel', lang)}",
                    callback_data=f"menu_page:{page}",
                )
            ]
        ]
    )


def amount_keyboard(
    suggested: float | None = None, page: int = 1
) -> InlineKeyboardMarkup:
    lang = get_lang()
    rows = []
    if suggested is not None:
        label = f"{suggested:.2f}".rstrip("0").rstrip(".")
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{t('transaction.suggestion', lang)} {label}",
                    callback_data=f"use_amount:{suggested}",
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=f"\u274c {t('common.cancel', lang)}",
                callback_data=f"menu_page:{page}",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def skip_keyboard(page: int = 1) -> InlineKeyboardMarkup:
    lang = get_lang()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"\u23ed\ufe0f {t('common.skip', lang)}",
                    callback_data="skip_default",
                ),
                InlineKeyboardButton(
                    text=f"\u274c {t('common.cancel', lang)}",
                    callback_data=f"menu_page:{page}",
                ),
            ]
        ]
    )


def confirm_keyboard(
    action: str, payload: str = "", page: int = 1
) -> InlineKeyboardMarkup:
    lang = get_lang()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"\u2705 {t('common.yes', lang)}",
                    callback_data=f"confirm_{action}:{payload}",
                ),
                InlineKeyboardButton(
                    text=f"\u274c {t('common.no', lang)}",
                    callback_data=f"menu_page:{page}",
                ),
            ]
        ]
    )


def category_keyboard(
    categories: list[str], add_new: bool = True, page: int = 1
) -> InlineKeyboardMarkup:
    lang = get_lang()
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
                    text=f"\u2795 {t('category.tg_new', get_lang())}",
                    callback_data="cat:__new__",
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=f"\u274c {t('common.cancel', lang)}",
                callback_data=f"menu_page:{page}",
            )
        ]
    )
    return rows_to_markup(rows)


def wallet_type_keyboard() -> InlineKeyboardMarkup:
    lang = get_lang()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"\U0001f45b {t('wallet.tg_regular', lang)}",
                    callback_data="wtype:regular",
                ),
                InlineKeyboardButton(
                    text=f"\U0001f3e6 {t('wallet.tg_deposit', lang)}",
                    callback_data="wtype:deposit",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"\u274c {t('common.cancel', lang)}", callback_data="wallets"
                )
            ],
        ]
    )


def wallet_list_keyboard(
    wallets: list[dict], action_prefix: str = "sw", menu_page: int = 3
) -> InlineKeyboardMarkup:
    lang = get_lang()
    rows = []
    for w in wallets:
        name = w["name"]
        label = f"{w['name']} ({w['currency']}) {w['balance']:.2f}"
        rows.append(
            [InlineKeyboardButton(text=label, callback_data=f"{action_prefix}:{name}")]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=f"\u2b05\ufe0f {t('common.menu', lang)}",
                callback_data=f"menu_page:{menu_page}",
            )
        ]
    )
    return rows_to_markup(rows)


def sorting_keyboard(
    options: dict[str, str], menu_page: int = 2
) -> InlineKeyboardMarkup:
    lang = get_lang()
    rows = [
        [InlineKeyboardButton(text=name, callback_data=f"sort:{key}")]
        for key, name in options.items()
    ]
    rows.append(
        [
            InlineKeyboardButton(
                text=f"\u2b05\ufe0f {t('common.menu', lang)}",
                callback_data=f"menu_page:{menu_page}",
            )
        ]
    )
    return rows_to_markup(rows)


def filter_menu_keyboard(menu_page: int = 2) -> InlineKeyboardMarkup:
    lang = get_lang()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"\U0001f4c5 {t('filter.tg_by_date', lang)}",
                    callback_data="filter:date",
                ),
                InlineKeyboardButton(
                    text=f"\U0001f4cb {t('filter.tg_by_type', lang)}",
                    callback_data="filter:type",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"\U0001f3f7\ufe0f {t('filter.tg_by_category', lang)}",
                    callback_data="filter:category",
                ),
                InlineKeyboardButton(
                    text=f"\U0001f4b0 {t('filter.tg_by_amount', lang)}",
                    callback_data="filter:amount",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"\U0001f4dd {t('filter.tg_by_description', lang)}",
                    callback_data="filter:description",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"\U0001f441\ufe0f {t('filter.tg_view_active', lang)}",
                    callback_data="filter:view_active",
                ),
                InlineKeyboardButton(
                    text=f"\U0001f9f9 {t('filter.tg_clear_all', lang)}",
                    callback_data="filter:clear_all",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"\u2b05\ufe0f {t('common.menu', lang)}",
                    callback_data=f"menu_page:{menu_page}",
                )
            ],
        ]
    )


def date_filter_keyboard() -> InlineKeyboardMarkup:
    lang = get_lang()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("filter.date_today", lang), callback_data="df:today"
                ),
                InlineKeyboardButton(
                    text=t("filter.date_last_week", lang), callback_data="df:last_week"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t("filter.date_last_month", lang),
                    callback_data="df:last_month",
                ),
                InlineKeyboardButton(
                    text=t("filter.date_this_month", lang),
                    callback_data="df:this_month",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t("filter.date_last_year", lang), callback_data="df:last_year"
                ),
                InlineKeyboardButton(
                    text=t("filter.date_this_year", lang), callback_data="df:this_year"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"\u274c {t('common.cancel', lang)}", callback_data="filters"
                )
            ],
        ]
    )


def type_filter_keyboard() -> InlineKeyboardMarkup:
    lang = get_lang()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("filter.type_income", lang), callback_data="tf:income_only"
                ),
                InlineKeyboardButton(
                    text=t("filter.type_expense", lang), callback_data="tf:expense_only"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t("filter.type_transfers", lang),
                    callback_data="tf:transfers_only",
                ),
                InlineKeyboardButton(
                    text=t("filter.type_no_transfers", lang),
                    callback_data="tf:no_transfers",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t("filter.type_recurring", lang),
                    callback_data="tf:recurring_only",
                ),
                InlineKeyboardButton(
                    text=t("filter.type_non_recurring", lang),
                    callback_data="tf:non_recurring",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"\u274c {t('common.cancel', lang)}", callback_data="filters"
                )
            ],
        ]
    )


def amount_filter_keyboard() -> InlineKeyboardMarkup:
    lang = get_lang()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("filter.tg_large", lang),
                    callback_data="af:large_transactions",
                ),
                InlineKeyboardButton(
                    text=t("filter.tg_small", lang),
                    callback_data="af:small_transactions",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t("filter.tg_custom_large", lang),
                    callback_data="af:custom_large",
                ),
                InlineKeyboardButton(
                    text=t("filter.tg_custom_small", lang),
                    callback_data="af:custom_small",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"\u274c {t('common.cancel', lang)}", callback_data="filters"
                )
            ],
        ]
    )


def transaction_actions_keyboard(
    index: int, menu_page: int = 2
) -> InlineKeyboardMarkup:
    lang = get_lang()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"\u270f\ufe0f {t('common.edit', lang)}",
                    callback_data=f"edit_tx:{index}",
                ),
                InlineKeyboardButton(
                    text=f"\U0001f5d1\ufe0f {t('common.delete', lang)}",
                    callback_data=f"del_tx:{index}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"\u2b05\ufe0f {t('common.menu', lang)}",
                    callback_data=f"menu_page:{menu_page}",
                )
            ],
        ]
    )


def recurring_actions_keyboard(index: int, menu_page: int = 2) -> InlineKeyboardMarkup:
    lang = get_lang()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"\u270f\ufe0f {t('common.edit', lang)}",
                    callback_data=f"edit_rec:{index}",
                ),
                InlineKeyboardButton(
                    text=f"\U0001f5d1\ufe0f {t('common.delete', lang)}",
                    callback_data=f"del_rec:{index}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"\u2b05\ufe0f {t('common.menu', lang)}",
                    callback_data=f"menu_page:{menu_page}",
                )
            ],
        ]
    )


def wallet_actions_keyboard(name: str, menu_page: int = 3) -> InlineKeyboardMarkup:
    lang = get_lang()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"\U0001f500 {t('btn.switch_to', lang)}",
                    callback_data=f"sw:{name}",
                ),
                InlineKeyboardButton(
                    text=f"\u270f\ufe0f {t('common.edit', lang)}",
                    callback_data=f"edit_w:{name}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"\U0001f5d1\ufe0f {t('common.delete', lang)}",
                    callback_data=f"del_w:{name}",
                ),
                InlineKeyboardButton(
                    text=f"\u2b05\ufe0f {t('common.menu', lang)}",
                    callback_data=f"menu_page:{menu_page}",
                ),
            ],
        ]
    )


def delete_recurring_keyboard(index: int, menu_page: int = 2) -> InlineKeyboardMarkup:
    lang = get_lang()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("recurring.tg_template_only", lang),
                    callback_data=f"delrec_opt:{index}:1",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t("recurring.tg_template_future", lang),
                    callback_data=f"delrec_opt:{index}:2",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t("recurring.tg_template_all", lang),
                    callback_data=f"delrec_opt:{index}:3",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"\u274c {t('common.cancel', lang)}",
                    callback_data=f"menu_page:{menu_page}",
                )
            ],
        ]
    )


def frequency_keyboard(page: int = 1) -> InlineKeyboardMarkup:
    lang = get_lang()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("recurring.freq_daily", lang), callback_data="freq:daily"
                ),
                InlineKeyboardButton(
                    text=t("recurring.freq_weekly", lang), callback_data="freq:weekly"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t("recurring.freq_monthly", lang), callback_data="freq:monthly"
                ),
                InlineKeyboardButton(
                    text=t("recurring.freq_yearly", lang), callback_data="freq:yearly"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"\u274c {t('common.cancel', lang)}",
                    callback_data=f"menu_page:{page}",
                )
            ],
        ]
    )


def end_condition_keyboard(page: int = 1) -> InlineKeyboardMarkup:
    lang = get_lang()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("recurring.end_never", lang), callback_data="endc:never"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("recurring.end_on_date", lang), callback_data="endc:on_date"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("recurring.end_after_count", lang),
                    callback_data="endc:after_count",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"\u274c {t('common.cancel', lang)}",
                    callback_data=f"menu_page:{page}",
                )
            ],
        ]
    )


def capitalization_keyboard() -> InlineKeyboardMarkup:
    lang = get_lang()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"\u2705 {t('common.yes', lang)}", callback_data="cap:yes"
                ),
                InlineKeyboardButton(
                    text=f"\u274c {t('common.no', lang)}", callback_data="cap:no"
                ),
            ],
        ]
    )


def edit_transaction_fields_keyboard(
    index: int, is_transfer: bool = False, menu_page: int = 2
) -> InlineKeyboardMarkup:
    lang = get_lang()
    rows = [
        [
            InlineKeyboardButton(
                text=t("btn.amount", lang), callback_data=f"etf:{index}:amount"
            )
        ],
    ]
    if not is_transfer:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t("btn.category", lang), callback_data=f"etf:{index}:category"
                )
            ]
        )
    rows.extend(
        [
            [
                InlineKeyboardButton(
                    text=t("btn.description", lang),
                    callback_data=f"etf:{index}:description",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("btn.date", lang), callback_data=f"etf:{index}:date"
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"\U0001f4be {t('common.save', lang)}",
                    callback_data=f"etf:{index}:save",
                ),
                InlineKeyboardButton(
                    text=f"\u274c {t('common.cancel', lang)}",
                    callback_data=f"menu_page:{menu_page}",
                ),
            ],
        ]
    )
    return rows_to_markup(rows)


def edit_wallet_fields_keyboard(name: str, menu_page: int = 3) -> InlineKeyboardMarkup:
    lang = get_lang()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("btn.name", lang), callback_data=f"ewf:{name}:name"
                ),
                InlineKeyboardButton(
                    text=t("btn.currency", lang), callback_data=f"ewf:{name}:currency"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t("btn.description", lang),
                    callback_data=f"ewf:{name}:description",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"\U0001f4be {t('common.save', lang)}",
                    callback_data=f"ewf:{name}:save",
                ),
                InlineKeyboardButton(
                    text=f"\u274c {t('common.cancel', lang)}",
                    callback_data=f"menu_page:{menu_page}",
                ),
            ],
        ]
    )


def edit_recurring_keyboard(index: int, menu_page: int = 2) -> InlineKeyboardMarkup:
    lang = get_lang()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"\u270f\ufe0f {t('recurring.tg_edit_template', lang)}",
                    callback_data=f"erec:{index}:template",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"\u23e9 {t('recurring.tg_skip_date', lang)}",
                    callback_data=f"erec:{index}:skip",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"\u23ef\ufe0f {t('recurring.tg_toggle', lang)}",
                    callback_data=f"erec:{index}:toggle",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"\u274c {t('common.cancel', lang)}",
                    callback_data=f"menu_page:{menu_page}",
                )
            ],
        ]
    )


def goal_menu_keyboard(menu_page: int = 2) -> InlineKeyboardMarkup:
    lang = get_lang()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"\U0001f3af {t('goal.tg_active', lang)}",
                    callback_data="goals:active",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"\u2705 {t('goal.tg_completed', lang)}",
                    callback_data="goals:completed",
                ),
                InlineKeyboardButton(
                    text=f"\U0001f4cb {t('goal.tg_all', lang)}",
                    callback_data="goals:all",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"\u2795 {t('goal.tg_add', lang)}",
                    callback_data="add_goal_start",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"\u2b05\ufe0f {t('common.menu', lang)}",
                    callback_data=f"menu_page:{menu_page}",
                )
            ],
        ]
    )


def goal_list_keyboard(
    goals: list[dict], action_prefix: str = "gdet"
) -> InlineKeyboardMarkup:
    lang = get_lang()
    rows = []
    for g in goals:
        goal = g.get("goal", {})
        progress = goal.get("progress", 0)
        name = g["name"]
        label = f"{name} ({progress:.0f}%)"
        rows.append(
            [InlineKeyboardButton(text=label, callback_data=f"{action_prefix}:{name}")]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=f"\u2795 {t('goal.tg_add', lang)}", callback_data="add_goal_start"
            ),
            InlineKeyboardButton(
                text=f"\u2b05\ufe0f {t('common.menu', lang)}",
                callback_data="goals_menu",
            ),
        ]
    )
    return rows_to_markup(rows)


def goal_actions_keyboard(name: str, status: str = "active") -> InlineKeyboardMarkup:
    lang = get_lang()
    rows = []
    if status == "active":
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"\U0001f4b0 {t('goal.tg_save_money', lang)}",
                    callback_data=f"gsave:{name}",
                ),
                InlineKeyboardButton(
                    text=f"\U0001f504 {t('goal.tg_recurring_save', lang)}",
                    callback_data=f"grecsave:{name}",
                ),
            ]
        )
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"\u2705 {t('goal.tg_complete', lang)}",
                    callback_data=f"gcomplete:{name}",
                )
            ]
        )
    elif status == "completed":
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"\U0001f6ab {t('goal.tg_hide', lang)}",
                    callback_data=f"ghide:{name}",
                ),
                InlineKeyboardButton(
                    text=f"\U0001f504 {t('goal.tg_reactivate', lang)}",
                    callback_data=f"greactivate:{name}",
                ),
            ]
        )
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"\U0001f5d1\ufe0f {t('goal.tg_delete', lang)}",
                    callback_data=f"gdel:{name}",
                )
            ]
        )
    elif status == "hidden":
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"\U0001f504 {t('goal.tg_reactivate', lang)}",
                    callback_data=f"greactivate:{name}",
                ),
                InlineKeyboardButton(
                    text=f"\U0001f5d1\ufe0f {t('goal.tg_delete', lang)}",
                    callback_data=f"gdel:{name}",
                ),
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=f"\u2b05\ufe0f {t('btn.goals', lang)}",
                callback_data="goals:active",
            )
        ]
    )
    return rows_to_markup(rows)


def bill_menu_keyboard(menu_page: int = 3) -> InlineKeyboardMarkup:
    lang = get_lang()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"\U0001f4cb {t('bill.tg_active', lang)}",
                    callback_data="bills:active",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"\u2705 {t('bill.tg_completed', lang)}",
                    callback_data="bills:completed",
                ),
                InlineKeyboardButton(
                    text=f"\U0001f4cb {t('bill.tg_all', lang)}",
                    callback_data="bills:all",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"\u2795 {t('bill.tg_add', lang)}",
                    callback_data="add_bill_start",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"\u2b05\ufe0f {t('common.menu', lang)}",
                    callback_data=f"menu_page:{menu_page}",
                )
            ],
        ]
    )


def bill_list_keyboard(
    bills: list[dict], action_prefix: str = "bdet"
) -> InlineKeyboardMarkup:
    lang = get_lang()
    rows = []
    for b in bills:
        bill = b.get("bill", {})
        progress = bill.get("progress", 0)
        name = b["name"]
        label = f"{name} ({progress:.0f}%)"
        rows.append(
            [InlineKeyboardButton(text=label, callback_data=f"{action_prefix}:{name}")]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=f"\u2795 {t('bill.tg_add', lang)}", callback_data="add_bill_start"
            ),
            InlineKeyboardButton(
                text=f"\u2b05\ufe0f {t('common.menu', lang)}",
                callback_data="bills_menu",
            ),
        ]
    )
    return rows_to_markup(rows)


def bill_actions_keyboard(name: str, status: str = "active") -> InlineKeyboardMarkup:
    lang = get_lang()
    rows = []
    if status == "active":
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"\U0001f4b0 {t('bill.tg_pay_money', lang)}",
                    callback_data=f"bpay:{name}",
                ),
            ]
        )
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"\u2705 {t('bill.tg_complete', lang)}",
                    callback_data=f"bcomplete:{name}",
                )
            ]
        )
    elif status == "completed":
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"\U0001f6ab {t('bill.tg_hide', lang)}",
                    callback_data=f"bhide:{name}",
                ),
                InlineKeyboardButton(
                    text=f"\U0001f504 {t('bill.tg_reactivate', lang)}",
                    callback_data=f"breactivate:{name}",
                ),
            ]
        )
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"\U0001f5d1\ufe0f {t('bill.tg_delete', lang)}",
                    callback_data=f"bdel:{name}",
                )
            ]
        )
    elif status == "hidden":
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"\U0001f504 {t('bill.tg_reactivate', lang)}",
                    callback_data=f"breactivate:{name}",
                ),
                InlineKeyboardButton(
                    text=f"\U0001f5d1\ufe0f {t('bill.tg_delete', lang)}",
                    callback_data=f"bdel:{name}",
                ),
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=f"\u2b05\ufe0f {t('btn.bills', lang)}",
                callback_data="bills:active",
            )
        ]
    )
    return rows_to_markup(rows)


def language_keyboard(current: str = "en-US", page: int = 1) -> InlineKeyboardMarkup:
    lang = get_lang()
    languages = {
        "en-US": "English (US)",
        "en-UK": "English (UK)",
        "ru-RU": "Русский",
    }
    rows = []
    for code, name in languages.items():
        marker = " \u2705" if code == current else ""
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{name}{marker}", callback_data=f"setlang:{code}"
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=f"\u2b05\ufe0f {t('common.menu', lang)}",
                callback_data=f"menu_page:{page}",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def timezone_keyboard(
    current: int = 0, page: int = 1, tz_page: int = 0
) -> InlineKeyboardMarkup:
    lang = get_lang()
    offsets = list(range(-12, 15))
    page_size = 9
    start = tz_page * page_size
    end = start + page_size
    page_offsets = offsets[start:end]

    rows = []
    row = []
    for offset in page_offsets:
        sign = "+" if offset >= 0 else ""
        label = f"GMT{sign}{offset}"
        marker = " \u2705" if offset == current else ""
        row.append(
            InlineKeyboardButton(
                text=f"{label}{marker}",
                callback_data=f"settz:{offset}@{page}",
            )
        )
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    nav = []
    if tz_page > 0:
        nav.append(
            InlineKeyboardButton(
                text=f"<< {t('common.prev', lang)}",
                callback_data=f"tzpage:{tz_page - 1}@{page}",
            )
        )
    if end < len(offsets):
        nav.append(
            InlineKeyboardButton(
                text=f"{t('common.next', lang)} >>",
                callback_data=f"tzpage:{tz_page + 1}@{page}",
            )
        )
    if nav:
        rows.append(nav)

    rows.append(
        [
            InlineKeyboardButton(
                text=f"\u2b05\ufe0f {t('common.menu', lang)}",
                callback_data=f"menu_page:{page}",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def chart_categories_keyboard(
    categories: dict,
    hidden: dict,
    page: int = 1,
) -> InlineKeyboardMarkup:
    """Build a keyboard to toggle chart category visibility.

    *categories* has keys ``expense`` and ``income``, each a list of
    category names.  *hidden* has the same structure — categories that
    are currently hidden.
    """
    lang = get_lang()
    rows: list[list[InlineKeyboardButton]] = []

    expense_cats = categories.get("expense", [])
    income_cats = categories.get("income", [])
    hidden_expense = hidden.get("expense", [])
    hidden_income = hidden.get("income", [])

    if expense_cats:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"--- {t('chart_categories.expenses', lang)} ---",
                    callback_data="noop",
                )
            ]
        )
        for cat in expense_cats:
            icon = "\u2b1c" if cat in hidden_expense else "\u2705"
            rows.append(
                [
                    InlineKeyboardButton(
                        text=f"{icon} {cat}",
                        callback_data=f"chtog:expense:{cat}@{page}",
                    )
                ]
            )

    if income_cats:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"--- {t('chart_categories.income', lang)} ---",
                    callback_data="noop",
                )
            ]
        )
        for cat in income_cats:
            icon = "\u2b1c" if cat in hidden_income else "\u2705"
            rows.append(
                [
                    InlineKeyboardButton(
                        text=f"{icon} {cat}",
                        callback_data=f"chtog:income:{cat}@{page}",
                    )
                ]
            )

    rows.append(
        [
            InlineKeyboardButton(
                text=f"\u2b05\ufe0f {t('common.menu', lang)}",
                callback_data=f"menu_page:{page}",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def rows_to_markup(rows: list[list[InlineKeyboardButton]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=rows)
