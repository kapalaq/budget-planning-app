"""Formatting helpers for Telegram messages.

Strategy: build plain text with <<b>>...<</b>> and <<c>>...<<c>> placeholders
for bold and inline-code, then escape everything in one pass at the end via
_to_md2(). This guarantees every special character from user data is escaped
without manual per-field handling.
"""

import re

from languages import t

# Sentinel markers that won't appear in real data
_B_OPEN = "\x00B\x00"  # bold open  -> *
_B_CLOSE = "\x01B\x01"  # bold close -> *
_I_OPEN = "\x00I\x00"  # italic open  -> _
_I_CLOSE = "\x01I\x01"  # italic close -> _
_C_OPEN = "\x00C\x00"  # code open  -> `
_C_CLOSE = "\x01C\x01"  # code close -> `

# MarkdownV2 special characters (everything that Telegram requires escaped)
_MD2_SPECIAL = re.compile(r"([_*\[\]()~`>#+\-=|{}.!\\])")


def _italic(text: str) -> str:
    return f"{_I_OPEN}{text}{_I_CLOSE}"


def _bold(text: str) -> str:
    return f"{_B_OPEN}{text}{_B_CLOSE}"


def _code(text: str) -> str:
    return f"{_C_OPEN}{text}{_C_CLOSE}"


def _to_md2(text: str) -> str:
    """Escape all MarkdownV2 specials, then restore bold/code markers."""
    # 1. Escape every special character
    escaped = _MD2_SPECIAL.sub(r"\\\1", text)
    # 2. Restore our markers to real MarkdownV2 syntax
    escaped = escaped.replace(_esc_sentinel(_B_OPEN), "*")
    escaped = escaped.replace(_esc_sentinel(_B_CLOSE), "*")
    escaped = escaped.replace(_esc_sentinel(_I_OPEN), "_")
    escaped = escaped.replace(_esc_sentinel(_I_CLOSE), "_")
    escaped = escaped.replace(_esc_sentinel(_C_OPEN), "`")
    escaped = escaped.replace(_esc_sentinel(_C_CLOSE), "`")
    return escaped


def _esc_sentinel(s: str) -> str:
    """Our sentinels contain no special chars, but the escaping pass may
    insert backslashes around them — this accounts for that."""
    # The sentinel chars (\x00, \x01) are not in _MD2_SPECIAL so they pass
    # through unchanged. The letters B/C are also not special. So sentinels
    # survive the escaping pass as-is.
    return s


def _fmtn(v: float) -> str:
    """Format a number, stripping trailing zeros (5.00 -> 5, 5.30 -> 5.3)."""
    return f"{v:.2f}".rstrip("0").rstrip(".")


# ── Public formatters ────────────────────────────────────────────────


def fmt_dashboard(data: dict, lang: str = "en-US") -> str:
    has_filters = data.get("has_filters", False)
    wallet_name = data["wallet_name"]
    currency = data["currency"]

    header = "\U0001f45b " + _bold(wallet_name)
    if has_filters:
        header += " \U0001f50d " + t("dashboard.filtered", lang)

    lines = [header, ""]

    if has_filters:
        lines.append(
            t("dashboard.filters_label", lang, summary=data.get("filter_summary", ""))
        )
        lines.append(
            t(
                "dashboard.showing",
                lang,
                filtered=data["filter_count"],
                total=data["total_count"],
            )
        )
        lines.append("")

    balance = data["balance"]
    sign = "+" if balance >= 0 else ""
    label = (
        t("dashboard.period_balance", lang)
        if has_filters
        else t("dashboard.balance", lang)
    )
    lines.append(f"\U0001f4b0 {_bold(label + ':')} {sign}{balance:.2f} {currency}")
    lines.append(
        f"  \U0001f4b5 {t('dashboard.income_label', lang)}  +{data['total_income']:.2f}"
    )
    lines.append(
        f"  \U0001f4b8 {t('dashboard.expense_label', lang)} -{data['total_expense']:.2f}"
    )
    if has_filters:
        ob = data["overall_balance"]
        os_sign = "+" if ob >= 0 else ""
        lines.append(f"  {t('dashboard.overall', lang, balance=f'{os_sign}{ob:.2f}')}")

    inc_cat = data.get("income_by_category", {})
    exp_cat = data.get("expense_by_category", {})
    inc_pct = data.get("income_percentages", {})
    exp_pct = data.get("expense_percentages", {})

    if inc_cat:
        lines.append("")
        lines.append(_bold(f"\U0001f4b5 {t('dashboard.income_by_cat', lang)}"))
        for cat, amt in sorted(inc_cat.items(), key=lambda x: -x[1]):
            pct = inc_pct.get(cat, 0)
            lines.append(f"  {cat}: +{amt:.2f} ({pct:.1f}%)")
    if exp_cat:
        lines.append("")
        lines.append(_bold(f"\U0001f4b8 {t('dashboard.expense_by_cat', lang)}"))
        for cat, amt in sorted(exp_cat.items(), key=lambda x: -x[1]):
            pct = exp_pct.get(cat, 0)
            lines.append(f"  {cat}: -{amt:.2f} ({pct:.1f}%)")

    active_goals = data.get("active_goals", [])
    if active_goals:
        lines.append("")
        lines.append(_bold(f"\U0001f3af {t('dashboard.active_goals', lang)}"))
        for g in active_goals:
            progress = g.get("progress", 0)
            bar_len = 8
            filled = int(bar_len * min(progress, 100) / 100)
            bar = "\u2588" * filled + "\u2591" * (bar_len - filled)
            lines.append(
                f"  {g['name']}: {_fmtn(g['saved'])}/{_fmtn(g['target'])} "
                f"{g['currency']} {bar} {progress:.0f}%"
            )

    transactions = data.get("transactions", [])
    strat = data.get("sorting_strategy", "")
    lines.append("")
    lines.append(
        f"\U0001f4cb {_bold(t('btn.transactions', lang))} ({t('dashboard.transactions_header', lang, strategy=strat).split('(', 1)[-1]}"
    )
    if not transactions:
        lines.append(f"  \U0001f4ed {t('dashboard.no_transactions', lang)}")
    else:
        for i, tx in enumerate(transactions, 1):
            rec_marker = " \U0001f504" if tx.get("recurrence_id") else ""
            lines.append(f"  {_code(f'{i}.')} {tx['display']}{rec_marker}")

    return _to_md2("\n".join(lines))


def fmt_portfolio(data: dict, lang: str = "en-US") -> str:
    base = data["base_currency"]
    total = data["total_balance"]
    wallets = data.get("wallets", [])
    rates_ok = data.get("rates_available", True)

    lines = [_bold(f"\U0001f4b1 {t('portfolio.title', lang)}"), ""]
    for w in wallets:
        sign = "+" if w["balance"] >= 0 else ""
        line = f"  {w['name']}: {sign}{w['balance']:.2f} {w['currency']}"
        if w["currency"] != base:
            line += f" ({w['converted']:.2f} {base})"
        lines.append(line)
    lines.append("")
    total_sign = "+" if total >= 0 else ""
    lines.append(
        _bold(
            f"\U0001f4b0 {t('portfolio.total', lang)}: {total_sign}{total:.2f} {base}"
        )
    )
    if not rates_ok:
        lines.append(f"\n\u26a0\ufe0f {t('portfolio.rates_unavailable', lang)}")
    return _to_md2("\n".join(lines))


def fmt_transaction(data: dict, lang: str = "en-US") -> str:
    sign = data["sign"]
    na = t("common.na", lang)
    lines = []
    if data["is_transfer"]:
        direction = (
            "\u2b06\ufe0f "
            + t("transaction.type_transfer_out", lang).split("(")[-1].rstrip(")")
            if data["transaction_type"] == "-"
            else "\u2b07\ufe0f "
            + t("transaction.type_transfer_in", lang).split("(")[-1].rstrip(")")
        )
        lines.append(_bold(f"\U0001f500 {t('transfer.title', lang)} ({direction})"))
        amount_str = f"{sign}{abs(data['amount']):.2f}"
        if data.get("cross_currency") and data.get("connected_amount") is not None:
            other_cur = data.get("connected_currency", "")
            amount_str += f" ({abs(data['connected_amount']):.2f} {other_cur})"
        lines.append(f"\U0001f4b2 {t('transaction.field_amount', lang)}: {amount_str}")
        lines.append(
            f"\U0001f4e4 {t('transaction.field_from', lang)}: {data.get('from_wallet', '?')}"
        )
        lines.append(
            f"\U0001f4e5 {t('transaction.field_to', lang)}: {data.get('to_wallet', '?')}"
        )
        lines.append(
            f"\U0001f4dd {t('transaction.field_description', lang)}: {data.get('description') or na}"
        )
        lines.append(f"\U0001f4c5 {t('transaction.field_date', lang)}: {data['date']}")
    else:
        if data["transaction_type"] == "+":
            type_label = f"\U0001f4b5 {t('common.income', lang)}"
        else:
            type_label = f"\U0001f4b8 {t('common.expense', lang)}"
        if data.get("recurrence_id"):
            type_label += " \U0001f504"
        lines.append(_bold(type_label))
        lines.append(
            f"\U0001f4b2 {t('transaction.field_amount', lang)}: {sign}{abs(data['amount']):.2f}"
        )
        lines.append(
            f"\U0001f3f7\ufe0f {t('transaction.field_category', lang)}: {data['category']}"
        )
        lines.append(
            f"\U0001f4dd {t('transaction.field_description', lang)}: {data.get('description') or na}"
        )
        lines.append(f"\U0001f4c5 {t('transaction.field_date', lang)}: {data['date']}")
    return _to_md2("\n".join(lines))


def fmt_wallets(data: dict, lang: str = "en-US") -> str:
    wallets = data["wallets"]
    current = data.get("current_wallet_name", "")
    lines = [
        f"\U0001f45b {_bold(t('btn.wallets', lang))} ({t('dashboard.transactions_header', lang, strategy=data.get('sorting_strategy', '')).split('(', 1)[-1]}",
        "",
    ]
    if not wallets:
        lines.append(f"\U0001f4ed {t('wallet.no_wallets', lang)}")
        return _to_md2("\n".join(lines))
    for i, w in enumerate(wallets, 1):
        marker = " \u2b05\ufe0f" if current and w["name"] == current else ""
        sign = "+" if w["balance"] >= 0 else ""
        tag = "\U0001f3e6" if w["wallet_type"] == "deposit" else "\U0001f45b"
        lines.append(
            f"  {_code(f'{i}.')} {tag} {w['name']} ({w['currency']}) "
            f"{sign}{w['balance']:.2f}{marker}"
        )
    if current:
        lines.append(f"\n  \u27a1\ufe0f Current: {current}")
    return _to_md2("\n".join(lines))


def fmt_wallet_detail(data: dict, lang: str = "en-US") -> str:
    wt = data["wallet_type"].capitalize()
    b = data["balance"]
    sign = "+" if b >= 0 else ""
    na = t("common.na", lang)
    wallet_icon = "\U0001f3e6" if data["wallet_type"] == "deposit" else "\U0001f45b"
    lines = [
        _bold(f"{wallet_icon} {wt} {t('wallet.field_name', lang)}: {data['name']}"),
        f"\U0001f4b1 {t('wallet.field_currency', lang)}: {data['currency']}",
        f"\U0001f4dd {t('wallet.field_description', lang)}: {data.get('description') or na}",
        f"\U0001f4b0 {t('wallet.field_balance', lang)}: {sign}{b:.2f}",
        f"\U0001f4b5 {t('wallet.field_income', lang)}: +{data['total_income']:.2f}",
        f"\U0001f4b8 {t('wallet.field_expense', lang)}: -{data['total_expense']:.2f}",
        f"\U0001f4cb {t('wallet.field_transactions', lang)}: {data['transaction_count']}",
    ]
    dep = data.get("deposit")
    if dep:
        lines.append("")
        lines.append(_bold(f"\U0001f3e6 {t('wallet.deposit_title', lang)}:"))
        lines.append(
            f"  {t('wallet.deposit_rate', lang)}: {dep['interest_rate']:.2f}% / year"
        )
        lines.append(f"  {t('wallet.deposit_term', lang)}: {dep['term_months']} months")
        cap_str = (
            t("common.yes", lang) if dep["capitalization"] else t("common.no", lang)
        )
        lines.append(f"  {t('wallet.deposit_capitalization', lang)}: {cap_str}")
        lines.append(f"  {t('wallet.deposit_maturity', lang)}: {dep['maturity_date']}")
        if dep["is_matured"]:
            lines.append(
                f"  \u2705 {t('goal.field_status', lang)}: {t('wallet.deposit_matured', lang)}"
            )
        else:
            lines.append(
                f"  {t('wallet.deposit_days', lang)}: {dep['days_until_maturity']}"
            )
        lines.append(f"  {t('wallet.deposit_principal', lang)}: {dep['principal']:.2f}")
        lines.append(
            f"  {t('wallet.deposit_interest', lang)}: {dep['accrued_interest']:.2f}"
        )
        lines.append(
            f"  {t('wallet.deposit_total', lang)}: {dep['maturity_amount']:.2f}"
        )
    return _to_md2("\n".join(lines))


def fmt_percentages(data: dict, lang: str = "en-US") -> str:
    if data.get("empty"):
        return _to_md2(data["message"])
    lines = [_bold(f"\U0001f4ca {t('percent.title', lang)}")]
    if data.get("has_filters"):
        lines[0] += f" \U0001f50d {t('dashboard.filtered', lang)}"
        lines.append(
            t("dashboard.filters_label", lang, summary=data.get("filter_summary", ""))
        )
    if data.get("income_percentages"):
        lines.append("")
        lines.append(_bold(f"\U0001f4b5 {t('percent.income', lang)}"))
        for cat, pct in sorted(data["income_percentages"].items(), key=lambda x: -x[1]):
            lines.append(f"  {cat}: {pct:.1f}%")
    if data.get("expense_percentages"):
        lines.append("")
        lines.append(_bold(f"\U0001f4b8 {t('percent.expenses', lang)}"))
        for cat, pct in sorted(
            data["expense_percentages"].items(), key=lambda x: -x[1]
        ):
            lines.append(f"  {cat}: {pct:.1f}%")
    return _to_md2("\n".join(lines))


def fmt_recurring_list(items: list[dict], lang: str = "en-US") -> str:
    if not items:
        return _to_md2(f"\U0001f4ed {t('recurring.no_recurring', lang)}")
    lines = [_bold(f"\U0001f504 {t('recurring.title', lang)}:"), ""]
    for i, r in enumerate(items, 1):
        lines.append(f"  {_code(f'{i}.')} {r['summary']}")
    return _to_md2("\n".join(lines))


def fmt_help(commands: list[dict]) -> str:
    lines = [_bold("\u2753 Available Commands:"), ""]
    for c in commands:
        lines.append(f"  {_code('/' + c['command'])} - {c['description']}")
    return _to_md2("\n".join(lines))


def fmt_goals(
    goals: list[dict], filter_label: str = "Active", lang: str = "en-US"
) -> str:
    if not goals:
        return _to_md2(
            f"\U0001f3af {t('goal.no_goals', lang, filter=filter_label.lower())}"
        )
    goals_label = t("btn.goals", lang)
    lines = [f"\U0001f3af {_bold(f'{filter_label} {goals_label}:')}", ""]
    for i, g in enumerate(goals, 1):
        goal = g.get("goal", {})
        target = goal.get("target", 0)
        saved = goal.get("saved", 0)
        progress = goal.get("progress", 0)
        status = goal.get("status", "active")
        bar_len = 10
        filled = int(bar_len * min(progress, 100) / 100)
        bar = "\u2588" * filled + "\u2591" * (bar_len - filled)
        status_marker = ""
        if status == "completed":
            status_marker = " \u2705"
        elif status == "hidden":
            status_marker = " \U0001f6ab"
        lines.append(f"  {_code(f'{i}.')} {g['name']}{status_marker}")
        lines.append(f"     {_fmtn(saved)} / {_fmtn(target)} {g['currency']}")
        lines.append(f"     {bar} {progress:.0f}%")
    return _to_md2("\n".join(lines))


def fmt_goal_detail(data: dict, lang: str = "en-US") -> str:
    goal = data.get("goal", {})
    target = goal.get("target", 0)
    saved = goal.get("saved", 0)
    progress = goal.get("progress", 0)
    remaining = goal.get("remaining", 0)
    bar_len = 15
    filled = int(bar_len * min(progress, 100) / 100)
    bar = "\u2588" * filled + "\u2591" * (bar_len - filled)
    lines = [
        _bold(f"\U0001f3af {data['name']}"),
        f"\U0001f4cb {t('goal.field_status', lang)}: {goal.get('status', 'active').upper()}",
        f"\U0001f3af {t('goal.field_target', lang)}: {_fmtn(target)} {data['currency']}",
        f"\U0001f4b0 {t('goal.field_saved', lang)}: {_fmtn(saved)} {data['currency']}",
        f"\U0001f4c9 {t('goal.field_remaining', lang)}: {_fmtn(remaining)} {data['currency']}",
        f"\U0001f4ca {t('goal.field_progress', lang)}: {bar} {progress:.0f}%",
    ]
    if goal.get("goal_description"):
        lines.append(f"\U0001f4dd {goal['goal_description']}")
    if goal.get("created_at"):
        lines.append(
            f"\U0001f4c5 {t('goal.field_created', lang)}: {goal['created_at']}"
        )
    if goal.get("completed_at"):
        lines.append(
            f"\u2705 {t('goal.field_completed', lang)}: {goal['completed_at']}"
        )
    return _to_md2("\n".join(lines))


def fmt_filters(filters: list[dict], lang: str = "en-US") -> str:
    if not filters:
        return _to_md2(f"\U0001f50d {t('filter.tg_no_active', lang)}")
    lines = [f"\U0001f50d {_bold(t('filter.active_title', lang))}", ""]
    for i, f in enumerate(filters, 1):
        lines.append(f"  {_code(f'{i}.')} {f['name']}: {f['description']}")
    return _to_md2("\n".join(lines))
