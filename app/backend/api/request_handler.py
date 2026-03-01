"""Request handler - middleground between Display (frontend) and business logic (backend)."""

from collections import defaultdict
from datetime import datetime
from typing import Dict, List

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
from wallet.wallet import DepositWallet, Wallet, WalletType
from wallet.wallet_manager import WalletManager


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
        }

    #  Public entry point
    def handle(self, request: dict) -> dict:
        """Route a request dict to the appropriate handler and return a response dict."""
        action = request.get("action")
        data = request.get("data", {})

        handler = self._routes.get(action)
        if handler:
            return handler(data)
        return {"status": "error", "message": f"Unknown action: {action}"}

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
        }
        return result

    #  Helpers
    def _current_wallet_or_error(self) -> tuple:
        """Return (wallet, None) or (None, error_response)."""
        wallet = self._wm.current_wallet
        if wallet is None:
            return None, {
                "status": "error",
                "message": "No wallet selected. Create or switch to a wallet first.",
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
            },
        }

    @staticmethod
    def _get_help(data: dict) -> dict:
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
            ("+r", "Add recurring income"),
            ("-r", "Add recurring expense"),
            ("recurring", "List recurring transactions"),
            ("show_rec <N>", "Show recurring details"),
            ("edit_rec <N>", "Edit recurring transaction"),
            ("delete_rec <N>", "Delete recurring transaction"),
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
            return {"status": "error", "message": f"Transaction #{index} not found"}
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
        return {"status": "success", "message": "Transaction added successfully!"}

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
                "Transfer updated successfully! (Both wallets have been synchronized)"
                if is_transfer
                else "Transaction updated successfully!"
            )
            return {"status": "success", "message": msg}
        return {"status": "error", "message": "Failed to update transaction"}

    def _delete_transaction(self, data: dict) -> dict:
        wallet, err = self._current_wallet_or_error()
        if err:
            return err

        index = data["index"]
        transaction = wallet.get_transaction(index)
        if transaction is None:
            return {"status": "error", "message": f"Transaction #{index} not found"}

        if wallet.delete_transaction(index):
            return {"status": "success", "message": "Transaction deleted successfully!"}
        return {"status": "error", "message": "Failed to delete transaction"}

    #  Transfer
    def _get_transfer_context(self, data: dict) -> dict:
        wallet, err = self._current_wallet_or_error()
        if err:
            return err
        if self._wm.wallet_count() < 2:
            return {
                "status": "error",
                "message": "You need at least two wallets to make a transfer.",
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
                "message": (
                    f"Transferred {data['amount']:.2f} from "
                    f"'{wallet.name}' to '{data['target_wallet_name']}'!"
                ),
            }
        return {"status": "error", "message": "Failed to complete transfer"}

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
                "message": f"Sorting changed to: {wallet.sorting_context.current_strategy.name}",
            }
        return {"status": "error", "message": "Invalid sorting option"}

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
                "message": (
                    f"Wallet sorting changed to: "
                    f"{self._wm.sorting_context.current_strategy.name}"
                ),
            }
        return {"status": "error", "message": "Invalid sorting option"}

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
        elif ft == "large":
            return LargeTransactionsFilter(threshold=data.get("threshold", 10000))
        elif ft == "small":
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
            return {"status": "error", "message": "Invalid filter type"}
        wallet.filtering_context.add_filter(filter_obj)
        return {
            "status": "success",
            "message": f"Added filter: {filter_obj.name}",
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
                "message": "Filter removed",
                "data": {"transactions": self._wallet_transactions(wallet)},
            }
        return {"status": "error", "message": "Failed to remove filter"}

    def _clear_filters(self, data: dict) -> dict:
        wallet, err = self._current_wallet_or_error()
        if err:
            return err
        wallet.filtering_context.clear_filters()
        return {
            "status": "success",
            "message": "All filters cleared",
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
                "No transactions match current filters"
                if has_filters
                else "No transactions to calculate percentages"
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
            return {"status": "error", "message": f"Wallet '{name}' not found"}
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
                "message": f"Wallet '{new_wallet.name}' created successfully!",
            }
        return {
            "status": "error",
            "message": f"Wallet with name '{data['name']}' already exists",
        }

    def _edit_wallet(self, data: dict) -> dict:
        name = data["name"]
        wallet = self._wm.get_wallet(name)
        if wallet is None:
            return {"status": "error", "message": f"Wallet '{name}' not found"}

        if self._wm.update_wallet(
            old_name=name,
            new_name=data.get("new_name"),
            currency=data.get("currency"),
            description=data.get("description"),
        ):
            return {"status": "success", "message": "Wallet updated successfully!"}
        return {
            "status": "error",
            "message": "Failed to update wallet. Name may already be in use.",
        }

    def _delete_wallet(self, data: dict) -> dict:
        name = data["name"]
        wallet = self._wm.get_wallet(name)
        if wallet is None:
            return {"status": "error", "message": f"Wallet '{name}' not found"}

        if self._wm.remove_wallet(name):
            return {
                "status": "success",
                "message": f"Wallet '{name}' deleted successfully!",
            }
        return {"status": "error", "message": "Failed to delete wallet"}

    def _switch_wallet(self, data: dict) -> dict:
        name = data["name"]
        if self._wm.switch_wallet(name):
            return {
                "status": "success",
                "message": f"Switched to wallet '{name}'",
            }
        return {"status": "error", "message": f"Wallet '{name}' not found"}

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
            "message": f"Recurring transaction created! ({count} transaction(s) generated)",
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
                "message": f"Recurring transaction #{index} not found",
            }
        return {"status": "success", "data": self._serialize_recurring(recurring)}

    def _edit_recurring(self, data: dict) -> dict:
        index = data["index"]
        scheduler = self._wm.recurrence_scheduler
        recurring = scheduler.get_recurring_by_index(index)
        if recurring is None:
            return {
                "status": "error",
                "message": f"Recurring transaction #{index} not found",
            }

        action = data.get("edit_action")

        if action == "edit_template":
            recurring.amount = data.get("amount", recurring.amount)
            recurring.category = data.get("category", recurring.category)
            recurring.description = data.get("description", recurring.description)
            return {
                "status": "success",
                "message": "Recurring transaction template updated!",
            }
        elif action == "skip_date":
            skip = data["date"]
            if isinstance(skip, str):
                skip = datetime.fromisoformat(skip)
            recurring.exceptions.add(skip)
            return {
                "status": "success",
                "message": f"Date {skip.strftime('%Y-%m-%d')} will be skipped",
            }
        elif action == "toggle_active":
            if recurring.is_active:
                scheduler.deactivate_recurring(recurring.id)
                return {"status": "success", "message": "Recurring transaction paused"}
            else:
                scheduler.activate_recurring(recurring.id)
                return {"status": "success", "message": "Recurring transaction resumed"}

        return {"status": "error", "message": "Invalid edit action"}

    def _delete_recurring(self, data: dict) -> dict:
        index = data["index"]
        scheduler = self._wm.recurrence_scheduler
        recurring = scheduler.get_recurring_by_index(index)
        if recurring is None:
            return {
                "status": "error",
                "message": f"Recurring transaction #{index} not found",
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
