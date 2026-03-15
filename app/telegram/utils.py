"""Formatting helpers for Telegram messages.

Strategy: build plain text with <<b>>...<</b>> and <<c>>...<<c>> placeholders
for bold and inline-code, then escape everything in one pass at the end via
_to_md2(). This guarantees every special character from user data is escaped
without manual per-field handling.
"""

import re

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


def fmt_dashboard(data: dict) -> str:
    has_filters = data.get("has_filters", False)
    wallet_name = data["wallet_name"]
    currency = data["currency"]

    header = "\U0001f45b " + _bold(wallet_name)
    if has_filters:
        header += " \U0001f50d [FILTERED]"

    lines = [header, ""]

    if has_filters:
        lines.append(f"Filters: {data.get('filter_summary', '')}")
        lines.append(
            f"Showing {data['filter_count']} of {data['total_count']} transactions"
        )
        lines.append("")

    balance = data["balance"]
    sign = "+" if balance >= 0 else ""
    label = "Period Balance" if has_filters else "Balance"
    lines.append(f"\U0001f4b0 {_bold(label + ':')} {sign}{balance:.2f} {currency}")
    lines.append(f"  \U0001f4b5 Income:  +{data['total_income']:.2f}")
    lines.append(f"  \U0001f4b8 Expense: -{data['total_expense']:.2f}")
    if has_filters:
        ob = data["overall_balance"]
        os_sign = "+" if ob >= 0 else ""
        lines.append(f"  (Overall: {os_sign}{ob:.2f})")

    inc_cat = data.get("income_by_category", {})
    exp_cat = data.get("expense_by_category", {})
    inc_pct = data.get("income_percentages", {})
    exp_pct = data.get("expense_percentages", {})

    if inc_cat:
        lines.append("")
        lines.append(_bold("\U0001f4b5 Income by Category:"))
        for cat, amt in sorted(inc_cat.items(), key=lambda x: -x[1]):
            pct = inc_pct.get(cat, 0)
            lines.append(f"  {cat}: +{amt:.2f} ({pct:.1f}%)")
    if exp_cat:
        lines.append("")
        lines.append(_bold("\U0001f4b8 Expenses by Category:"))
        for cat, amt in sorted(exp_cat.items(), key=lambda x: -x[1]):
            pct = exp_pct.get(cat, 0)
            lines.append(f"  {cat}: -{amt:.2f} ({pct:.1f}%)")

    active_goals = data.get("active_goals", [])
    if active_goals:
        lines.append("")
        lines.append(_bold("\U0001f3af Active Goals:"))
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
    lines.append(f"\U0001f4cb {_bold('Transactions')} (sorted by: {strat}):")
    if not transactions:
        lines.append("  \U0001f4ed No transactions")
    else:
        for i, t in enumerate(transactions, 1):
            rec_marker = " \U0001f504" if t.get("recurrence_id") else ""
            lines.append(f"  {_code(f'{i}.')} {t['display']}{rec_marker}")

    return _to_md2("\n".join(lines))


def fmt_transaction(data: dict) -> str:
    sign = data["sign"]
    lines = []
    if data["is_transfer"]:
        direction = (
            "\u2b06\ufe0f Outgoing"
            if data["transaction_type"] == "-"
            else "\u2b07\ufe0f Incoming"
        )
        lines.append(_bold(f"\U0001f500 Transfer ({direction})"))
        lines.append(f"\U0001f4b2 Amount: {sign}{abs(data['amount']):.2f}")
        lines.append(f"\U0001f4e4 From: {data.get('from_wallet', '?')}")
        lines.append(f"\U0001f4e5 To: {data.get('to_wallet', '?')}")
        lines.append(f"\U0001f4dd Description: {data.get('description') or 'N/A'}")
        lines.append(f"\U0001f4c5 Date: {data['date']}")
    else:
        if data["transaction_type"] == "+":
            type_label = "\U0001f4b5 Income"
        else:
            type_label = "\U0001f4b8 Expense"
        if data.get("recurrence_id"):
            type_label += " \U0001f504"
        lines.append(_bold(type_label))
        lines.append(f"\U0001f4b2 Amount: {sign}{abs(data['amount']):.2f}")
        lines.append(f"\U0001f3f7\ufe0f Category: {data['category']}")
        lines.append(f"\U0001f4dd Description: {data.get('description') or 'N/A'}")
        lines.append(f"\U0001f4c5 Date: {data['date']}")
    return _to_md2("\n".join(lines))


def fmt_wallets(data: dict) -> str:
    wallets = data["wallets"]
    current = data.get("current_wallet_name", "")
    lines = [
        f"\U0001f45b {_bold('Wallets')} (sorted by: {data.get('sorting_strategy', '')}):",
        "",
    ]
    if not wallets:
        lines.append("\U0001f4ed No wallets")
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


def fmt_wallet_detail(data: dict) -> str:
    wt = data["wallet_type"].capitalize()
    b = data["balance"]
    sign = "+" if b >= 0 else ""
    wallet_icon = "\U0001f3e6" if data["wallet_type"] == "deposit" else "\U0001f45b"
    lines = [
        _bold(f"{wallet_icon} {wt} Wallet: {data['name']}"),
        f"\U0001f4b1 Currency: {data['currency']}",
        f"\U0001f4dd Description: {data.get('description') or 'N/A'}",
        f"\U0001f4b0 Balance: {sign}{b:.2f}",
        f"\U0001f4b5 Income: +{data['total_income']:.2f}",
        f"\U0001f4b8 Expense: -{data['total_expense']:.2f}",
        f"\U0001f4cb Transactions: {data['transaction_count']}",
    ]
    dep = data.get("deposit")
    if dep:
        lines.append("")
        lines.append(_bold("\U0001f3e6 Deposit Details:"))
        lines.append(f"  Interest Rate: {dep['interest_rate']:.2f}% / year")
        lines.append(f"  Term: {dep['term_months']} months")
        cap_str = "Yes" if dep["capitalization"] else "No"
        lines.append(f"  Capitalization: {cap_str}")
        lines.append(f"  Maturity: {dep['maturity_date']}")
        if dep["is_matured"]:
            lines.append("  \u2705 Status: MATURED")
        else:
            lines.append(f"  Days to Maturity: {dep['days_until_maturity']}")
        lines.append(f"  Principal: {dep['principal']:.2f}")
        lines.append(f"  Accrued Interest: {dep['accrued_interest']:.2f}")
        lines.append(f"  Total at Maturity: {dep['maturity_amount']:.2f}")
    return _to_md2("\n".join(lines))


def fmt_percentages(data: dict) -> str:
    if data.get("empty"):
        return _to_md2(data["message"])
    lines = [_bold("\U0001f4ca Category Percentages")]
    if data.get("has_filters"):
        lines[0] += " \U0001f50d [FILTERED]"
        lines.append(f"Filters: {data.get('filter_summary', '')}")
    if data.get("income_percentages"):
        lines.append("")
        lines.append(_bold("\U0001f4b5 Income:"))
        for cat, pct in sorted(data["income_percentages"].items(), key=lambda x: -x[1]):
            lines.append(f"  {cat}: {pct:.1f}%")
    if data.get("expense_percentages"):
        lines.append("")
        lines.append(_bold("\U0001f4b8 Expenses:"))
        for cat, pct in sorted(
            data["expense_percentages"].items(), key=lambda x: -x[1]
        ):
            lines.append(f"  {cat}: {pct:.1f}%")
    return _to_md2("\n".join(lines))


def fmt_recurring_list(items: list[dict]) -> str:
    if not items:
        return _to_md2("\U0001f4ed No recurring transactions")
    lines = [_bold("\U0001f504 Recurring Transactions:"), ""]
    for i, r in enumerate(items, 1):
        lines.append(f"  {_code(f'{i}.')} {r['summary']}")
    return _to_md2("\n".join(lines))


def fmt_help(commands: list[dict]) -> str:
    lines = [_bold("\u2753 Available Commands:"), ""]
    for c in commands:
        lines.append(f"  {_code('/' + c['command'])} - {c['description']}")
    return _to_md2("\n".join(lines))


def fmt_goals(goals: list[dict], filter_label: str = "Active") -> str:
    if not goals:
        return _to_md2(f"\U0001f3af No {filter_label.lower()} goals")
    lines = [f"\U0001f3af {_bold(f'{filter_label} Goals:')}", ""]
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


def fmt_goal_detail(data: dict) -> str:
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
        f"\U0001f4cb Status: {goal.get('status', 'active').upper()}",
        f"\U0001f3af Target: {_fmtn(target)} {data['currency']}",
        f"\U0001f4b0 Saved: {_fmtn(saved)} {data['currency']}",
        f"\U0001f4c9 Remaining: {_fmtn(remaining)} {data['currency']}",
        f"\U0001f4ca Progress: {bar} {progress:.0f}%",
    ]
    if goal.get("goal_description"):
        lines.append(f"\U0001f4dd {goal['goal_description']}")
    if goal.get("created_at"):
        lines.append(f"\U0001f4c5 Created: {goal['created_at']}")
    if goal.get("completed_at"):
        lines.append(f"\u2705 Completed: {goal['completed_at']}")
    return _to_md2("\n".join(lines))


def fmt_filters(filters: list[dict]) -> str:
    if not filters:
        return _to_md2("\U0001f50d No active filters")
    lines = [f"\U0001f50d {_bold('Active Filters:')}", ""]
    for i, f in enumerate(filters, 1):
        lines.append(f"  {_code(f'{i}.')} {f['name']}: {f['description']}")
    return _to_md2("\n".join(lines))
