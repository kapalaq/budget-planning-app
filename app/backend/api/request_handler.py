"""Request handler - middleground between Display (frontend) and business logic (backend)."""

from collections import defaultdict
from datetime import datetime
from typing import Dict, List

from languages import t
from models.recurrence import (
    EndCondition,
    Frequency,
    RecurrenceRule,
    RecurringTransaction,
    Weekday,
)
from models.transaction import Transaction, TransactionType, Transfer
from strategies.filtering import (
    AmountRangeFilter,
    CategoryFilter,
    DateRangeFilter,
    DescriptionFilter,
    ExpenseOnlyFilter,
    IncomeOnlyFilter,
    LargeTransactionsFilter,
    LastMonthFilter,
    LastWeekFilter,
    LastYearFilter,
    NonRecurringFilter,
    NoTransfersFilter,
    RecurringOnlyFilter,
    SmallTransactionsFilter,
    ThisMonthFilter,
    ThisYearFilter,
    TodayFilter,
    TransferOnlyFilter,
)
from strategies.sorting import SortingContext, WalletSortingContext
from wallet.wallet import DepositWallet, GoalStatus, Wallet, WalletType
from wallet.wallet_manager import WalletManager


def _fmt(v: float) -> str:
    """Format a number, stripping trailing zeros (5.00 -> 5, 5.30 -> 5.3)."""
    return f"{v:.2f}".rstrip("0").rstrip(".")


class RequestHandler:
    """Middleground that routes dict requests to business logic and returns dict responses."""

    def __init__(self, wallet_manager: WalletManager):
        self._wm = wallet_manager
        self._routes = {
            # Dashboard / general
            "get_dashboard": self._get_dashboard,
            "get_help": self._get_help,
            "process_recurring": self._process_recurring,
            # Transaction CRUD
            "get_categories": self._get_categories,
            "get_transaction": self._get_transaction,
            "add_transaction": self._add_transaction,
            "edit_transaction": self._edit_transaction,
            "delete_transaction": self._delete_transaction,
            # Transfer
            "get_transfer_context": self._get_transfer_context,
            "transfer": self._transfer,
            # Sorting
            "get_sorting_options": self._get_sorting_options,
            "set_sorting": self._set_sorting,
            "get_wallet_sorting_options": self._get_wallet_sorting_options,
            "set_wallet_sorting": self._set_wallet_sorting,
            # Filtering
            "add_filter": self._add_filter,
            "remove_filter": self._remove_filter,
            "clear_filters": self._clear_filters,
            "get_active_filters": self._get_active_filters,
            # Percentages
            "get_percentages": self._get_percentages,
            # Wallet CRUD
            "get_wallets": self._get_wallets,
            "get_wallet_detail": self._get_wallet_detail,
            "add_wallet": self._add_wallet,
            "edit_wallet": self._edit_wallet,
            "delete_wallet": self._delete_wallet,
            "switch_wallet": self._switch_wallet,
            # Recurring CRUD
            "add_recurring": self._add_recurring,
            "get_recurring_list": self._get_recurring_list,
            "get_recurring_detail": self._get_recurring_detail,
            "edit_recurring": self._edit_recurring,
            "delete_recurring": self._delete_recurring,
            # Recurring transfers
            "add_recurring_transfer": self._add_recurring_transfer,
            "add_recurring_goal_save": self._add_recurring_goal_save,
            # Goals
            "add_goal": self._add_goal,
            "get_goals": self._get_goals,
            "get_all_goals": self._get_all_goals,
            "get_goal_detail": self._get_goal_detail,
            "complete_goal": self._complete_goal,
            "hide_goal": self._hide_goal,
            "reactivate_goal": self._reactivate_goal,
            "save_to_goal": self._save_to_goal,
        }

    #  Public entry point
    def handle(self, request: dict, lang: str = "en-US") -> dict:
        """Route a request dict to the appropriate handler and return a response dict."""
        self._lang = lang
        action = request.get("action")
        data = request.get("data", {})

        handler = self._routes.get(action)
        if handler:
            return handler(data)
        return {"status": "error", "message": t("common.unknown_action", lang, action=action)}

    # ------------------------------------------------------------------ #
    #  Serialisation helpers                                              #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _serialize_transaction(t: Transaction) -> dict:
        sign = "+" if t.transaction_type == TransactionType.INCOME else "-"
        is_transfer = isinstance(t, Transfer)

        result = {
            "id": t.id,
            "amount": t.amount,
            "signed_amount": t.signed_amount,
            "transaction_type": t.transaction_type.value,
            "category": t.category,
            "description": t.description or "",
            "date": t.datetime_created.strftime("%Y-%m-%d %H:%M:%S"),
            "display": str(t),
            "recurrence_id": getattr(t, "recurrence_id", None),
            "is_transfer": is_transfer,
            "sign": sign,
        }

        if is_transfer:
            if t.transaction_type == TransactionType.EXPENSE:
                result["from_wallet"] = t.source.name if t.source else "Unknown"
                result["to_wallet"] = (
                    t.connected.source.name
                    if t.connected and t.connected.source
                    else "Unknown"
                )
            else:
                result["from_wallet"] = (
                    t.connected.source.name
                    if t.connected and t.connected.source
                    else "Unknown"
                )
                result["to_wallet"] = t.source.name if t.source else "Unknown"

        return result

    @staticmethod
    def _serialize_wallet(w: Wallet) -> dict:
        result = {
            "id": w.id,
            "name": w.name,
            "currency": w.currency,
            "balance": w.balance,
            "total_income": w.total_income,
            "total_expense": w.total_expense,
            "description": w.description or "",
            "transaction_count": w.transaction_count(),
            "wallet_type": w.wallet_type.value,
            "created": w.datetime_created.strftime("%Y-%m-%d %H:%M"),
            "is_goal_wallet": w.is_goal_wallet,
        }

        if isinstance(w, DepositWallet):
            result["deposit"] = {
                "interest_rate": w.interest_rate,
                "term_months": w.term_months,
                "capitalization": w.capitalization,
                "maturity_date": w.maturity_date.strftime("%Y-%m-%d"),
                "is_matured": w.is_matured,
                "days_until_maturity": w.days_until_maturity,
                "principal": w.principal,
                "accrued_interest": w.calculate_accrued_interest(),
                "maturity_amount": w.calculate_maturity_amount(),
            }

        if w.is_goal_wallet:
            target = w.goal_target or 0
            progress = (w.balance / target * 100) if target > 0 else 0
            result["goal"] = {
                "target": target,
                "goal_description": w.goal_description or "",
                "status": w.goal_status.value,
                "progress": min(progress, 100),
                "saved": w.balance,
                "remaining": max(target - w.balance, 0),
                "created_at": (
                    w.goal_created_at.strftime("%Y-%m-%d %H:%M")
                    if w.goal_created_at
                    else None
                ),
                "completed_at": (
                    w.goal_completed_at.strftime("%Y-%m-%d %H:%M")
                    if w.goal_completed_at
                    else None
                ),
            }

        return result

    @staticmethod
    def _serialize_recurring(r: RecurringTransaction) -> dict:
        sign = "+" if r.transaction_type == TransactionType.INCOME else "-"
        result = {
            "id": r.id,
            "amount": r.amount,
            "transaction_type": r.transaction_type.value,
            "category": r.category,
            "description": r.description or "",
            "wallet_name": r.wallet_name,
            "is_active": r.is_active,
            "generated_count": r.generated_count,
            "pattern_description": r.recurrence_rule.description(),
            "start_date": r.start_date.strftime("%Y-%m-%d"),
            "last_generated": (
                r.last_generated.strftime("%Y-%m-%d") if r.last_generated else None
            ),
            "summary": r.summary_str(),
            "detail": r.detailed_str(),
            "sign": sign,
            "is_transfer": r.is_transfer,
            "target_wallet_name": r.target_wallet_name,
        }
        return result

    #  Helpers
    def _current_wallet_or_error(self) -> tuple:
        """Return (wallet, None) or (None, error_response)."""
        wallet = self._wm.current_wallet
        if wallet is None:
            return None, {
                "status": "error",
                "message": t("wallet.no_wallet_selected", self._lang),
            }
        return wallet, None

    def _wallet_transactions(self, wallet: Wallet) -> List[dict]:
        """Get serialised transactions respecting current filters/sorting."""
        ctx = wallet.filtering_context
        if ctx.has_filters:
            transactions = wallet.get_filtered_transactions()
        else:
            transactions = wallet.get_sorted_transactions()
        return [self._serialize_transaction(t) for t in transactions]

    @staticmethod
    def _parse_transaction_type(value: str) -> TransactionType:
        if value in ("+", "income"):
            return TransactionType.INCOME
        return TransactionType.EXPENSE

    #  Dashboard / general
    def _get_dashboard(self, data: dict) -> dict:
        wallet, err = self._current_wallet_or_error()
        if err:
            return err

        ctx = wallet.filtering_context
        has_filters = ctx.has_filters

        if has_filters:
            transactions = wallet.get_filtered_transactions()
        else:
            transactions = wallet.get_sorted_transactions()

        # Calculate totals from the (possibly filtered) list
        total_income = 0.0
        total_expense = 0.0
        for t in transactions:
            if t.transaction_type == TransactionType.INCOME:
                total_income += t.amount
            else:
                total_expense += t.amount
        balance = total_income - total_expense

        # Category breakdown
        income_by_cat: Dict[str, float] = defaultdict(float)
        expense_by_cat: Dict[str, float] = defaultdict(float)
        for t in transactions:
            if t.transaction_type == TransactionType.INCOME:
                income_by_cat[t.category] += t.amount
            else:
                expense_by_cat[t.category] += t.amount

        income_pct = {}
        expense_pct = {}
        if total_income > 0:
            income_pct = {c: (a / total_income) * 100 for c, a in income_by_cat.items()}
        if total_expense > 0:
            expense_pct = {
                c: (a / total_expense) * 100 for c, a in expense_by_cat.items()
            }

        # Active goals summary
        active_goals = self._wm.get_active_goals()
        goals_data = []
        for g in active_goals:
            target = g.goal_target or 0
            progress = (g.balance / target * 100) if target > 0 else 0
            goals_data.append(
                {
                    "name": g.name,
                    "currency": g.currency,
                    "target": target,
                    "saved": g.balance,
                    "progress": min(progress, 100),
                    "remaining": max(target - g.balance, 0),
                }
            )

        return {
            "status": "success",
            "data": {
                "wallet_name": wallet.name,
                "currency": wallet.currency,
                "balance": balance if has_filters else wallet.balance,
                "total_income": total_income if has_filters else wallet.total_income,
                "total_expense": total_expense if has_filters else wallet.total_expense,
                "overall_balance": wallet.balance,
                "has_filters": has_filters,
                "filter_summary": ctx.filter_summary if has_filters else None,
                "filter_count": len(transactions),
                "total_count": wallet.transaction_count(),
                "sorting_strategy": wallet.sorting_context.current_strategy.name,
                "transactions": [self._serialize_transaction(t) for t in transactions],
                "income_by_category": dict(income_by_cat),
                "expense_by_category": dict(expense_by_cat),
                "income_percentages": income_pct,
                "expense_percentages": expense_pct,
                "active_goals": goals_data,
            },
        }

    def _get_help(self, data: dict) -> dict:
        commands = [
            ("+", "Add income transaction"),
            ("-", "Add expense transaction"),
            ("transfer", "Transfer money between wallets"),
            ("show <N>", "Show details of transaction N"),
            ("edit <N>", "Edit transaction N"),
            ("delete <N>", "Delete transaction N"),
            ("sort", "Change sorting method"),
            ("filter", "Filter transactions"),
            ("percent", "Show category percentages"),
            ("wallets", "Show all wallets"),
            ("add_wallet", "Add a new wallet"),
            ("wallet <name>", "Show wallet details"),
            ("edit_wallet <name>", "Edit a wallet"),
            ("delete_wallet <name>", "Delete a wallet"),
            ("switch <name>", "Switch to a wallet"),
            ("sort_wallets", "Change wallet sorting"),
            ("goals", "View savings goals"),
            ("add_goal", "Create a savings goal"),
            ("save <name>", "Save money to a goal"),
            ("+r", "Add recurring income"),
            ("-r", "Add recurring expense"),
            ("recurring_transfer", "Add recurring transfer"),
            ("recurring", "List recurring transactions"),
            ("show_rec <N>", "Show recurring details"),
            ("edit_rec <N>", "Edit recurring transaction"),
            ("delete_rec <N>", "Delete recurring transaction"),
            ("language", "Change language"),
            ("home", "Show dashboard"),
            ("help", "Show this help message"),
            ("quit", "Exit the program"),
        ]
        return {
            "status": "success",
            "data": {
                "commands": [{"command": c, "description": d} for c, d in commands]
            },
        }

    def _process_recurring(self, data: dict) -> dict:
        scheduler = self._wm.recurrence_scheduler
        generated = scheduler.process_due_transactions()
        return {
            "status": "success",
            "data": {"generated_count": generated},
        }

    #  Transaction CRUD
    def _get_categories(self, data: dict) -> dict:
        wallet, err = self._current_wallet_or_error()
        if err:
            return err
        tt = self._parse_transaction_type(data.get("transaction_type", "expense"))
        categories = sorted(wallet.category_manager.get_categories(tt))
        return {"status": "success", "data": {"categories": categories}}

    def _get_transaction(self, data: dict) -> dict:
        wallet, err = self._current_wallet_or_error()
        if err:
            return err
        index = data.get("index")
        transaction = wallet.get_transaction(index)
        if transaction is None:
            return {"status": "error", "message": t("transaction.not_found", self._lang, index=index)}
        return {
            "status": "success",
            "data": self._serialize_transaction(transaction),
        }

    def _add_transaction(self, data: dict) -> dict:
        wallet, err = self._current_wallet_or_error()
        if err:
            return err

        tt = self._parse_transaction_type(data["transaction_type"])

        date = data.get("date")
        if isinstance(date, str):
            date = datetime.fromisoformat(date)
        elif date is None:
            date = datetime.now()

        transaction = Transaction(
            amount=data["amount"],
            transaction_type=tt,
            category=data["category"],
            description=data.get("description", ""),
            datetime_created=date,
        )
        wallet.add_transaction(transaction)
        return {"status": "success", "message": t("transaction.added", self._lang)}

    def _edit_transaction(self, data: dict) -> dict:
        wallet, err = self._current_wallet_or_error()
        if err:
            return err

        index = data["index"]
        transaction = wallet.get_transaction(index)
        if transaction is None:
            return {"status": "error", "message": f"Transaction #{index} not found"}

        date = data.get("date")
        if isinstance(date, str):
            date = datetime.fromisoformat(date)
        elif date is None:
            date = transaction.datetime_created

        updated = Transaction(
            amount=data.get("amount", transaction.amount),
            transaction_type=transaction.transaction_type,
            category=data.get("category", transaction.category),
            description=data.get("description", transaction.description),
            datetime_created=date,
        )

        if wallet.update_transaction(index, updated):
            is_transfer = isinstance(transaction, Transfer)
            msg = (
                t("transaction.transfer_updated", self._lang)
                if is_transfer
                else t("transaction.updated", self._lang)
            )
            return {"status": "success", "message": msg}
        return {"status": "error", "message": t("transaction.not_found", self._lang, index=index)}

    def _delete_transaction(self, data: dict) -> dict:
        wallet, err = self._current_wallet_or_error()
        if err:
            return err

        index = data["index"]
        transaction = wallet.get_transaction(index)
        if transaction is None:
            return {"status": "error", "message": t("transaction.not_found", self._lang, index=index)}

        if wallet.delete_transaction(index):
            return {"status": "success", "message": t("transaction.deleted", self._lang)}
        return {"status": "error", "message": t("transaction.deleted", self._lang)}

    #  Transfer
    def _get_transfer_context(self, data: dict) -> dict:
        wallet, err = self._current_wallet_or_error()
        if err:
            return err
        if self._wm.wallet_count() < 2:
            return {
                "status": "error",
                "message": t("transfer.need_two_wallets", self._lang),
            }
        available = self._wm.get_sorted_wallets()
        targets = [w for w in available if w.name != wallet.name]
        return {
            "status": "success",
            "data": {
                "from_wallet": self._serialize_wallet(wallet),
                "target_wallets": [self._serialize_wallet(w) for w in targets],
            },
        }

    def _transfer(self, data: dict) -> dict:
        wallet, err = self._current_wallet_or_error()
        if err:
            return err

        date = data.get("date")
        if isinstance(date, str):
            date = datetime.fromisoformat(date)

        if self._wm.transfer(
            from_wallet_name=wallet.name,
            to_wallet_name=data["target_wallet_name"],
            amount=data["amount"],
            description=data.get("description", ""),
            datetime_created=date,
        ):
            return {
                "status": "success",
                "message": t("transfer.success", self._lang, amount=f"{data['amount']:.2f}", from_wallet=wallet.name, to_wallet=data['target_wallet_name']),
            }
        return {"status": "error", "message": t("transfer.failed", self._lang)}

    #  Sorting
    def _get_sorting_options(self, data: dict) -> dict:
        strategies = SortingContext.get_available_strategies()
        return {
            "status": "success",
            "data": {"options": strategies},
        }

    def _set_sorting(self, data: dict) -> dict:
        wallet, err = self._current_wallet_or_error()
        if err:
            return err
        key = data["strategy_key"]
        if wallet.sorting_context.set_strategy(key):
            return {
                "status": "success",
                "message": t("sorting.changed", self._lang, name=wallet.sorting_context.current_strategy.name),
            }
        return {"status": "error", "message": t("sorting.invalid", self._lang)}

    def _get_wallet_sorting_options(self, data: dict) -> dict:
        strategies = WalletSortingContext.get_available_strategies()
        return {
            "status": "success",
            "data": {"options": strategies},
        }

    def _set_wallet_sorting(self, data: dict) -> dict:
        key = data["strategy_key"]
        if self._wm.sorting_context.set_strategy(key):
            return {
                "status": "success",
                "message": t("sorting.wallet_changed", self._lang, name=self._wm.sorting_context.current_strategy.name),
            }
        return {"status": "error", "message": t("sorting.invalid", self._lang)}

    # ------------------------------------------------------------------ #
    #  Filtering                                                          #
    # ------------------------------------------------------------------ #

    def _create_filter(self, data: dict):
        """Create a FilterStrategy from a dict description."""
        ft = data["filter_type"]

        if ft == "today":
            return TodayFilter()
        elif ft == "last_week":
            return LastWeekFilter()
        elif ft == "last_month":
            return LastMonthFilter()
        elif ft == "this_month":
            return ThisMonthFilter()
        elif ft == "last_year":
            return LastYearFilter()
        elif ft == "this_year":
            return ThisYearFilter()
        elif ft == "date_range":
            start = data.get("start_date")
            end = data.get("end_date")
            if isinstance(start, str):
                start = datetime.fromisoformat(start)
            if isinstance(end, str):
                end = datetime.fromisoformat(end)
            return DateRangeFilter(start_date=start, end_date=end)
        elif ft == "income_only":
            return IncomeOnlyFilter(
                include_transfers=data.get("include_transfers", True)
            )
        elif ft == "expense_only":
            return ExpenseOnlyFilter(
                include_transfers=data.get("include_transfers", True)
            )
        elif ft == "transfers_only":
            return TransferOnlyFilter()
        elif ft == "no_transfers":
            return NoTransfersFilter()
        elif ft == "recurring_only":
            return RecurringOnlyFilter()
        elif ft == "non_recurring":
            return NonRecurringFilter()
        elif ft == "category":
            return CategoryFilter(
                categories=set(data["categories"]),
                mode=data.get("mode", "include"),
            )
        elif ft == "large_transactions":
            return LargeTransactionsFilter(threshold=data.get("threshold", 10000))
        elif ft == "small_transactions":
            return SmallTransactionsFilter(threshold=data.get("threshold", 100))
        elif ft == "amount_range":
            return AmountRangeFilter(
                min_amount=data.get("min_amount"),
                max_amount=data.get("max_amount"),
            )
        elif ft == "description":
            return DescriptionFilter(
                search_term=data["search_term"],
                case_sensitive=data.get("case_sensitive", False),
            )
        return None

    def _add_filter(self, data: dict) -> dict:
        wallet, err = self._current_wallet_or_error()
        if err:
            return err
        filter_obj = self._create_filter(data)
        if filter_obj is None:
            return {"status": "error", "message": t("filter.invalid_type", self._lang)}
        wallet.filtering_context.add_filter(filter_obj)
        return {
            "status": "success",
            "message": t("filter.added", self._lang, name=filter_obj.name),
            "data": {"transactions": self._wallet_transactions(wallet)},
        }

    def _remove_filter(self, data: dict) -> dict:
        wallet, err = self._current_wallet_or_error()
        if err:
            return err
        idx = data["filter_index"]
        if wallet.filtering_context.remove_filter(idx):
            return {
                "status": "success",
                "message": t("filter.removed", self._lang),
                "data": {"transactions": self._wallet_transactions(wallet)},
            }
        return {"status": "error", "message": t("filter.remove_failed", self._lang)}

    def _clear_filters(self, data: dict) -> dict:
        wallet, err = self._current_wallet_or_error()
        if err:
            return err
        wallet.filtering_context.clear_filters()
        return {
            "status": "success",
            "message": t("filter.all_cleared", self._lang),
            "data": {"transactions": self._wallet_transactions(wallet)},
        }

    def _get_active_filters(self, data: dict) -> dict:
        wallet, err = self._current_wallet_or_error()
        if err:
            return err
        filters = wallet.filtering_context.active_filters
        return {
            "status": "success",
            "data": {
                "filters": [
                    {"name": f.name, "description": f.description} for f in filters
                ]
            },
        }

    #  Percentages
    def _get_percentages(self, data: dict) -> dict:
        wallet, err = self._current_wallet_or_error()
        if err:
            return err

        has_filters = wallet.filtering_context.has_filters
        if has_filters:
            transactions = wallet.get_filtered_transactions()
            income_by_cat: Dict[str, float] = defaultdict(float)
            expense_by_cat: Dict[str, float] = defaultdict(float)
            for t in transactions:
                if t.transaction_type == TransactionType.INCOME:
                    income_by_cat[t.category] += t.amount
                else:
                    expense_by_cat[t.category] += t.amount
            total_income = sum(income_by_cat.values())
            total_expense = sum(expense_by_cat.values())
            income_pct = (
                {c: (a / total_income) * 100 for c, a in income_by_cat.items()}
                if total_income > 0
                else {}
            )
            expense_pct = (
                {c: (a / total_expense) * 100 for c, a in expense_by_cat.items()}
                if total_expense > 0
                else {}
            )
        else:
            income_pct = wallet.get_income_percentages()
            expense_pct = wallet.get_expense_percentages()

        if not income_pct and not expense_pct:
            msg = (
                t("dashboard.no_match_filters", self._lang)
                if has_filters
                else t("dashboard.no_transactions", self._lang)
            )
            return {"status": "success", "data": {"empty": True, "message": msg}}

        return {
            "status": "success",
            "data": {
                "has_filters": has_filters,
                "filter_summary": (
                    wallet.filtering_context.filter_summary if has_filters else None
                ),
                "income_percentages": income_pct,
                "expense_percentages": expense_pct,
            },
        }

    #  Wallet CRUD
    def _get_wallets(self, data: dict) -> dict:
        wallets = self._wm.get_sorted_wallets()
        current = self._wm.current_wallet
        return {
            "status": "success",
            "data": {
                "wallets": [self._serialize_wallet(w) for w in wallets],
                "current_wallet_name": current.name if current else None,
                "sorting_strategy": self._wm.sorting_context.current_strategy.name,
            },
        }

    def _get_wallet_detail(self, data: dict) -> dict:
        name = data["name"]
        wallet = self._wm.get_wallet(name)
        if wallet is None:
            return {"status": "error", "message": t("wallet.not_found", self._lang, name=name)}
        return {"status": "success", "data": self._serialize_wallet(wallet)}

    def _add_wallet(self, data: dict) -> dict:
        wallet_type_str = data.get("wallet_type", "regular")
        wallet_type = (
            WalletType.DEPOSIT if wallet_type_str == "deposit" else WalletType.REGULAR
        )

        if wallet_type == WalletType.DEPOSIT:
            new_wallet = DepositWallet(
                name=data["name"],
                interest_rate=data["interest_rate"],
                term_months=data["term_months"],
                starting_value=data.get("starting_value"),
                currency=data.get("currency", "KZT"),
                description=data.get("description", ""),
                capitalization=data.get("capitalization", False),
            )
        else:
            new_wallet = Wallet(
                name=data["name"],
                starting_value=data.get("starting_value"),
                currency=data.get("currency", "KZT"),
                description=data.get("description", ""),
            )

        if self._wm.add_wallet(new_wallet):
            return {
                "status": "success",
                "message": t("wallet.created", self._lang, name=new_wallet.name),
            }
        return {
            "status": "error",
            "message": t("wallet.already_exists", self._lang, name=data['name']),
        }

    def _edit_wallet(self, data: dict) -> dict:
        name = data["name"]
        wallet = self._wm.get_wallet(name)
        if wallet is None:
            return {"status": "error", "message": t("wallet.not_found", self._lang, name=name)}

        if self._wm.update_wallet(
            old_name=name,
            new_name=data.get("new_name"),
            currency=data.get("currency"),
            description=data.get("description"),
        ):
            return {"status": "success", "message": t("wallet.updated", self._lang)}
        return {
            "status": "error",
            "message": t("wallet.update_failed", self._lang),
        }

    def _delete_wallet(self, data: dict) -> dict:
        name = data["name"]
        wallet = self._wm.get_wallet(name)
        if wallet is None:
            return {"status": "error", "message": t("wallet.not_found", self._lang, name=name)}

        if wallet.is_goal_wallet and wallet.goal_status == GoalStatus.ACTIVE:
            return {
                "status": "error",
                "message": t("wallet.cannot_delete_goal", self._lang),
            }

        if self._wm.remove_wallet(name, force=True):
            return {
                "status": "success",
                "message": t("wallet.deleted", self._lang, name=name),
            }
        return {"status": "error", "message": t("wallet.delete_failed", self._lang)}

    def _switch_wallet(self, data: dict) -> dict:
        name = data["name"]
        if self._wm.switch_wallet(name):
            return {
                "status": "success",
                "message": t("wallet.switched", self._lang, name=name),
            }
        return {"status": "error", "message": t("wallet.not_found", self._lang, name=name)}

    #  Recurring CRUD
    @staticmethod
    def _build_recurrence_rule(rule_data: dict) -> RecurrenceRule:
        """Build a RecurrenceRule from a dict."""
        freq = Frequency(rule_data["frequency"])
        weekdays = set()
        for wd_val in rule_data.get("weekdays", []):
            weekdays.add(Weekday(wd_val))

        rule = RecurrenceRule(
            frequency=freq,
            interval=rule_data.get("interval", 1),
            weekdays=weekdays,
            month_week=rule_data.get("month_week"),
            month_weekday=(
                Weekday(rule_data["month_weekday"])
                if rule_data.get("month_weekday") is not None
                else None
            ),
        )

        end = rule_data.get("end_condition", "never")
        if end == "on_date":
            rule.end_condition = EndCondition.ON_DATE
            ed = rule_data["end_date"]
            rule.end_date = datetime.fromisoformat(ed) if isinstance(ed, str) else ed
        elif end == "after_count":
            rule.end_condition = EndCondition.AFTER_COUNT
            rule.max_occurrences = rule_data["max_occurrences"]

        return rule

    def _add_recurring(self, data: dict) -> dict:
        wallet, err = self._current_wallet_or_error()
        if err:
            return err

        tt = self._parse_transaction_type(data["transaction_type"])

        start_date = data.get("start_date")
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date)
        elif start_date is None:
            start_date = datetime.now()

        rule = self._build_recurrence_rule(data["recurrence_rule"])

        recurring = RecurringTransaction(
            amount=data["amount"],
            transaction_type=tt,
            category=data["category"],
            description=data.get("description", ""),
            recurrence_rule=rule,
            start_date=start_date,
            wallet_name=wallet.name,
        )

        scheduler = self._wm.recurrence_scheduler
        scheduler.add_recurring(recurring)
        count = scheduler.process_due_transactions()

        return {
            "status": "success",
            "message": t("recurring.created", self._lang, count=count),
        }

    def _get_recurring_list(self, data: dict) -> dict:
        scheduler = self._wm.recurrence_scheduler
        recurring_list = scheduler.get_all_recurring()
        return {
            "status": "success",
            "data": {
                "recurring_transactions": [
                    self._serialize_recurring(r) for r in recurring_list
                ]
            },
        }

    def _get_recurring_detail(self, data: dict) -> dict:
        index = data["index"]
        scheduler = self._wm.recurrence_scheduler
        recurring = scheduler.get_recurring_by_index(index)
        if recurring is None:
            return {
                "status": "error",
                "message": t("recurring.not_found", self._lang, index=index),
            }
        return {"status": "success", "data": self._serialize_recurring(recurring)}

    def _edit_recurring(self, data: dict) -> dict:
        index = data["index"]
        scheduler = self._wm.recurrence_scheduler
        recurring = scheduler.get_recurring_by_index(index)
        if recurring is None:
            return {
                "status": "error",
                "message": t("recurring.not_found", self._lang, index=index),
            }

        action = data.get("edit_action")

        if action == "edit_template":
            recurring.amount = data.get("amount", recurring.amount)
            recurring.category = data.get("category", recurring.category)
            recurring.description = data.get("description", recurring.description)
            return {
                "status": "success",
                "message": t("recurring.template_updated", self._lang),
            }
        elif action == "skip_date":
            skip = data["date"]
            if isinstance(skip, str):
                skip = datetime.fromisoformat(skip)
            recurring.exceptions.add(skip)
            return {
                "status": "success",
                "message": t("recurring.date_skipped", self._lang, date=skip.strftime('%Y-%m-%d')),
            }
        elif action == "toggle_active":
            if recurring.is_active:
                scheduler.deactivate_recurring(recurring.id)
                return {"status": "success", "message": t("recurring.paused", self._lang)}
            else:
                scheduler.activate_recurring(recurring.id)
                return {"status": "success", "message": t("recurring.resumed", self._lang)}

        return {"status": "error", "message": t("recurring.invalid_edit", self._lang)}

    def _delete_recurring(self, data: dict) -> dict:
        index = data["index"]
        scheduler = self._wm.recurrence_scheduler
        recurring = scheduler.get_recurring_by_index(index)
        if recurring is None:
            return {
                "status": "error",
                "message": t("recurring.not_found", self._lang, index=index),
            }

        delete_option = data.get("delete_option", 1)
        rec_id = recurring.id
        wallet = self._wm.get_wallet(recurring.wallet_name)
        info_messages = []

        if delete_option == 2 and wallet:
            deleted = wallet.delete_future_by_recurrence(rec_id)
            info_messages.append(f"Removed {deleted} future transaction(s)")
        elif delete_option == 3 and wallet:
            all_rec = wallet.get_transactions_by_recurrence(rec_id)
            for t in all_rec:
                wallet.delete_transaction(t.id)
            info_messages.append(f"Removed {len(all_rec)} generated transaction(s)")

        scheduler.remove_recurring(rec_id)
        info_messages.append("Recurring transaction deleted!")

        return {
            "status": "success",
            "message": " ".join(info_messages),
        }

    # ------------------------------------------------------------------ #
    #  Recurring transfers                                                 #
    # ------------------------------------------------------------------ #

    def _add_recurring_transfer(self, data: dict) -> dict:
        """Create a recurring transfer between two wallets."""
        wallet, err = self._current_wallet_or_error()
        if err:
            return err

        target_name = data.get("target_wallet_name", "")
        target = self._wm.get_wallet(target_name)
        if target is None:
            return {
                "status": "error",
                "message": t("transfer.target_not_found", self._lang, name=target_name),
            }

        if target.name.lower() == wallet.name.lower():
            return {"status": "error", "message": t("transfer.cannot_same", self._lang)}

        amount = data.get("amount")
        if amount is None or amount <= 0:
            return {"status": "error", "message": t("common.amount_positive", self._lang)}

        start_date = data.get("start_date")
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date)
        elif start_date is None:
            start_date = datetime.now()

        rule = self._build_recurrence_rule(data["recurrence_rule"])

        recurring = RecurringTransaction(
            amount=amount,
            transaction_type=TransactionType.EXPENSE,
            category="Transfer",
            description=data.get("description", f"Transfer to {target.name}"),
            recurrence_rule=rule,
            start_date=start_date,
            wallet_name=wallet.name,
            target_wallet_name=target.name,
        )

        scheduler = self._wm.recurrence_scheduler
        scheduler.add_recurring(recurring)
        count = scheduler.process_due_transactions()

        return {
            "status": "success",
            "message": t("recurring.created", self._lang, count=count),
        }

    def _add_recurring_goal_save(self, data: dict) -> dict:
        """Create a recurring save-to-goal (recurring transfer to goal wallet)."""
        wallet, err = self._current_wallet_or_error()
        if err:
            return err

        goal_name = data.get("goal_name", "")
        goal_wallet = self._wm.get_wallet(goal_name)
        if goal_wallet is None or not goal_wallet.is_goal_wallet:
            return {"status": "error", "message": t("goal.not_found", self._lang, name=goal_name)}

        amount = data.get("amount")
        if amount is None or amount <= 0:
            return {"status": "error", "message": t("common.amount_positive", self._lang)}

        start_date = data.get("start_date")
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date)
        elif start_date is None:
            start_date = datetime.now()

        rule = self._build_recurrence_rule(data["recurrence_rule"])

        recurring = RecurringTransaction(
            amount=amount,
            transaction_type=TransactionType.EXPENSE,
            category="Transfer",
            description=data.get("description", f"Saving to {goal_name}"),
            recurrence_rule=rule,
            start_date=start_date,
            wallet_name=wallet.name,
            target_wallet_name=goal_wallet.name,
        )

        scheduler = self._wm.recurrence_scheduler
        scheduler.add_recurring(recurring)
        count = scheduler.process_due_transactions()

        return {
            "status": "success",
            "message": t("recurring.created", self._lang, count=count),
        }

    # ------------------------------------------------------------------ #
    #  Goals                                                               #
    # ------------------------------------------------------------------ #

    def _add_goal(self, data: dict) -> dict:
        name = data.get("name", "").strip()
        if not name:
            return {"status": "error", "message": t("goal.name_empty", self._lang)}

        target = data.get("target")
        if target is None or target <= 0:
            return {"status": "error", "message": t("goal.target_positive", self._lang)}

        wallet_name = f"Goal: {name}"
        new_wallet = Wallet(
            name=wallet_name,
            currency=data.get("currency", "KZT"),
            description=data.get("description", ""),
            is_goal_wallet=True,
            goal_target=target,
            goal_description=data.get("goal_description", name),
        )

        if self._wm.add_wallet(new_wallet):
            return {
                "status": "success",
                "message": t("goal.created", self._lang, name=name, amount=_fmt(target)),
                "data": self._serialize_wallet(new_wallet),
            }
        return {
            "status": "error",
            "message": t("goal.wallet_exists", self._lang, name=wallet_name),
        }

    def _get_goals(self, data: dict) -> dict:
        filter_status = data.get("filter", "active")
        if filter_status == "active":
            goals = self._wm.get_active_goals()
        elif filter_status == "completed":
            goals = self._wm.get_completed_goals()
        elif filter_status == "all":
            goals = self._wm.get_all_goals()
        else:
            goals = self._wm.get_active_goals()

        return {
            "status": "success",
            "data": {
                "goals": [self._serialize_wallet(g) for g in goals],
                "filter": filter_status,
            },
        }

    def _get_all_goals(self, data: dict) -> dict:
        goals = self._wm.get_all_goals()
        return {
            "status": "success",
            "data": {
                "goals": [self._serialize_wallet(g) for g in goals],
                "filter": "all",
            },
        }

    def _get_goal_detail(self, data: dict) -> dict:
        name = data.get("name", "")
        wallet = self._wm.get_wallet(name)
        if wallet is None:
            return {"status": "error", "message": t("goal.not_found", self._lang, name=name)}
        if not wallet.is_goal_wallet:
            return {"status": "error", "message": t("goal.not_goal_wallet", self._lang, name=name)}
        return {"status": "success", "data": self._serialize_wallet(wallet)}

    def _complete_goal(self, data: dict) -> dict:
        name = data.get("name", "")
        if self._wm.complete_goal(name):
            return {
                "status": "success",
                "message": t("goal.completed", self._lang),
            }
        wallet = self._wm.get_wallet(name)
        if wallet is None:
            return {"status": "error", "message": t("goal.not_found", self._lang, name=name)}
        if not wallet.is_goal_wallet:
            return {"status": "error", "message": t("goal.not_goal_wallet", self._lang, name=name)}
        return {"status": "error", "message": t("goal.not_active", self._lang)}

    def _hide_goal(self, data: dict) -> dict:
        name = data.get("name", "")
        if self._wm.hide_goal(name):
            return {"status": "success", "message": t("goal.hidden", self._lang)}
        return {"status": "error", "message": t("goal.cannot_hide", self._lang)}

    def _reactivate_goal(self, data: dict) -> dict:
        name = data.get("name", "")
        if self._wm.reactivate_goal(name):
            return {"status": "success", "message": t("goal.reactivated", self._lang)}
        return {"status": "error", "message": t("goal.cannot_reactivate", self._lang)}

    def _save_to_goal(self, data: dict) -> dict:
        """Transfer money from current wallet to a goal wallet."""
        wallet, err = self._current_wallet_or_error()
        if err:
            return err

        goal_name = data.get("goal_name", "")
        amount = data.get("amount")
        if amount is None or amount <= 0:
            return {"status": "error", "message": t("common.amount_positive", self._lang)}

        goal_wallet = self._wm.get_wallet(goal_name)
        if goal_wallet is None or not goal_wallet.is_goal_wallet:
            return {"status": "error", "message": t("goal.not_found", self._lang, name=goal_name)}

        if self._wm.transfer(
            from_wallet_name=wallet.name,
            to_wallet_name=goal_wallet.name,
            amount=amount,
            description=data.get("description", f"Saving to {goal_name}"),
        ):
            target = goal_wallet.goal_target or 0
            new_balance = goal_wallet.balance
            progress = (new_balance / target * 100) if target > 0 else 0
            return {
                "status": "success",
                "message": t("goal.save_success", self._lang, amount=_fmt(amount)),
                "data": {
                    "progress": f"{_fmt(new_balance)}/{_fmt(target)} ({progress:.0f}%)",
                },
            }
        return {"status": "error", "message": t("goal.save_failed", self._lang)}
