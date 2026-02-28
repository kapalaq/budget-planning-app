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
_C_OPEN = "\x00C\x00"  # code open  -> `
_C_CLOSE = "\x01C\x01"  # code close -> `

# MarkdownV2 special characters (everything that Telegram requires escaped)
_MD2_SPECIAL = re.compile(r"([_*\[\]()~`>#+\-=|{}.!\\])")


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


# ── Public formatters ────────────────────────────────────────────────


def fmt_dashboard(data: dict) -> str:
    has_filters = data.get("has_filters", False)
    wallet_name = data["wallet_name"]
    currency = data["currency"]

    header = _bold(wallet_name)
    if has_filters:
        header += " [FILTERED]"

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
    lines.append(f"{_bold(label + ':')} {sign}{balance:.2f} {currency}")
    lines.append(f"  Income:  +{data['total_income']:.2f}")
    lines.append(f"  Expense: -{data['total_expense']:.2f}")
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
        lines.append(_bold("Income by Category:"))
        for cat, amt in sorted(inc_cat.items(), key=lambda x: -x[1]):
            pct = inc_pct.get(cat, 0)
            lines.append(f"  {cat}: +{amt:.2f} ({pct:.1f}%)")
    if exp_cat:
        lines.append("")
        lines.append(_bold("Expenses by Category:"))
        for cat, amt in sorted(exp_cat.items(), key=lambda x: -x[1]):
            pct = exp_pct.get(cat, 0)
            lines.append(f"  {cat}: -{amt:.2f} ({pct:.1f}%)")

    transactions = data.get("transactions", [])
    strat = data.get("sorting_strategy", "")
    lines.append("")
    lines.append(f"{_bold('Transactions')} (sorted by: {strat}):")
    if not transactions:
        lines.append("  No transactions")
    else:
        for i, t in enumerate(transactions, 1):
            rec_marker = " (R)" if t.get("recurrence_id") else ""
            lines.append(f"  {_code(f'{i}.')} {t['display']}{rec_marker}")

    return _to_md2("\n".join(lines))


def fmt_transaction(data: dict) -> str:
    sign = data["sign"]
    lines = []
    if data["is_transfer"]:
        direction = "Outgoing" if data["transaction_type"] == "-" else "Incoming"
        lines.append(_bold(f"Transfer ({direction})"))
        lines.append(f"Amount: {sign}{abs(data['amount']):.2f}")
        lines.append(f"From: {data.get('from_wallet', '?')}")
        lines.append(f"To: {data.get('to_wallet', '?')}")
        lines.append(f"Description: {data.get('description') or 'N/A'}")
        lines.append(f"Date: {data['date']}")
    else:
        type_label = "Income" if data["transaction_type"] == "+" else "Expense"
        if data.get("recurrence_id"):
            type_label += " (Recurring)"
        lines.append(_bold(type_label))
        lines.append(f"Amount: {sign}{abs(data['amount']):.2f}")
        lines.append(f"Category: {data['category']}")
        lines.append(f"Description: {data.get('description') or 'N/A'}")
        lines.append(f"Date: {data['date']}")
    return _to_md2("\n".join(lines))


def fmt_wallets(data: dict) -> str:
    wallets = data["wallets"]
    current = data.get("current_wallet_name", "")
    lines = [
        f"{_bold('Wallets')} (sorted by: {data.get('sorting_strategy', '')}):",
        "",
    ]
    if not wallets:
        lines.append("No wallets")
        return _to_md2("\n".join(lines))
    for i, w in enumerate(wallets, 1):
        marker = " *" if current and w["name"] == current else ""
        sign = "+" if w["balance"] >= 0 else ""
        tag = "D" if w["wallet_type"] == "deposit" else "R"
        lines.append(
            f"  {_code(f'{i}.')} [{tag}] {w['name']} ({w['currency']}) "
            f"{sign}{w['balance']:.2f}{marker}"
        )
    if current:
        lines.append(f"\n  * Current: {current}")
    return _to_md2("\n".join(lines))


def fmt_wallet_detail(data: dict) -> str:
    wt = data["wallet_type"].capitalize()
    b = data["balance"]
    sign = "+" if b >= 0 else ""
    lines = [
        _bold(f"{wt} Wallet: {data['name']}"),
        f"Currency: {data['currency']}",
        f"Description: {data.get('description') or 'N/A'}",
        f"Balance: {sign}{b:.2f}",
        f"Income: +{data['total_income']:.2f}",
        f"Expense: -{data['total_expense']:.2f}",
        f"Transactions: {data['transaction_count']}",
    ]
    dep = data.get("deposit")
    if dep:
        lines.append("")
        lines.append(_bold("Deposit Details:"))
        lines.append(f"  Interest Rate: {dep['interest_rate']:.2f}% / year")
        lines.append(f"  Term: {dep['term_months']} months")
        cap_str = "Yes" if dep["capitalization"] else "No"
        lines.append(f"  Capitalization: {cap_str}")
        lines.append(f"  Maturity: {dep['maturity_date']}")
        if dep["is_matured"]:
            lines.append("  Status: MATURED")
        else:
            lines.append(f"  Days to Maturity: {dep['days_until_maturity']}")
        lines.append(f"  Principal: {dep['principal']:.2f}")
        lines.append(f"  Accrued Interest: {dep['accrued_interest']:.2f}")
        lines.append(f"  Total at Maturity: {dep['maturity_amount']:.2f}")
    return _to_md2("\n".join(lines))


def fmt_percentages(data: dict) -> str:
    if data.get("empty"):
        return _to_md2(data["message"])
    lines = [_bold("Category Percentages")]
    if data.get("has_filters"):
        lines[0] += " [FILTERED]"
        lines.append(f"Filters: {data.get('filter_summary', '')}")
    if data.get("income_percentages"):
        lines.append("")
        lines.append(_bold("Income:"))
        for cat, pct in sorted(data["income_percentages"].items(), key=lambda x: -x[1]):
            lines.append(f"  {cat}: {pct:.1f}%")
    if data.get("expense_percentages"):
        lines.append("")
        lines.append(_bold("Expenses:"))
        for cat, pct in sorted(
            data["expense_percentages"].items(), key=lambda x: -x[1]
        ):
            lines.append(f"  {cat}: {pct:.1f}%")
    return _to_md2("\n".join(lines))


def fmt_recurring_list(items: list[dict]) -> str:
    if not items:
        return _to_md2("No recurring transactions")
    lines = [_bold("Recurring Transactions:"), ""]
    for i, r in enumerate(items, 1):
        lines.append(f"  {_code(f'{i}.')} {r['summary']}")
    return _to_md2("\n".join(lines))


def fmt_help(commands: list[dict]) -> str:
    lines = [_bold("Available Commands:"), ""]
    for c in commands:
        lines.append(f"  {_code('/' + c['command'])} - {c['description']}")
    return _to_md2("\n".join(lines))


def fmt_filters(filters: list[dict]) -> str:
    if not filters:
        return _to_md2("No active filters")
    lines = [_bold("Active Filters:"), ""]
    for i, f in enumerate(filters, 1):
        lines.append(f"  {_code(f'{i}.')} {f['name']}: {f['description']}")
    return _to_md2("\n".join(lines))
