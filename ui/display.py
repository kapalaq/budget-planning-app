"""Display utilities for the budget planner."""
from collections import defaultdict
from typing import List, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from wallet.wallet_manager import WalletManager
    from models.recurrence import RecurringTransaction
from models.transaction import Transaction, TransactionType
from wallet.wallet import Wallet, DepositWallet, WalletType
from strategies.sorting import SortingContext, WalletSortingContext
from strategies.filtering import FilteringContext


class Display:
    """Handles all display/output operations."""
    
    SEPARATOR = "=" * 50
    
    @staticmethod
    def clear_screen():
        """Print some newlines to simulate clearing."""
        print("\n" * 2)
    
    @staticmethod
    def show_header(text: str):
        """Display a header."""
        print(f"\n{Display.SEPARATOR}")
        print(f"  {text}")
        print(Display.SEPARATOR)
    
    @staticmethod
    def _calculate_totals(transactions: List[Transaction]) -> Dict:
        """Calculate totals from a list of transactions."""
        total_income = 0.0
        total_expense = 0.0
        for t in transactions:
            if t.transaction_type == TransactionType.INCOME:
                total_income += t.amount
            else:
                total_expense += t.amount
        balance = total_income - total_expense
        return {
            "balance": balance,
            "total_income": total_income,
            "total_expense": total_expense,
        }

    @staticmethod
    def _calculate_category_breakdown(
        transactions: List[Transaction],
    ) -> Dict:
        """Calculate category breakdown from a list of transactions."""
        income_by_cat: Dict[str, float] = defaultdict(float)
        expense_by_cat: Dict[str, float] = defaultdict(float)

        for t in transactions:
            if t.transaction_type == TransactionType.INCOME:
                income_by_cat[t.category] += t.amount
            else:
                expense_by_cat[t.category] += t.amount

        # Filter out zero values
        income_by_cat = {k: v for k, v in income_by_cat.items() if v != 0}
        expense_by_cat = {k: v for k, v in expense_by_cat.items() if v != 0}

        # Calculate percentages
        total_income = sum(income_by_cat.values())
        total_expense = sum(expense_by_cat.values())

        income_pct = {}
        expense_pct = {}

        if total_income > 0:
            income_pct = {
                cat: (amt / total_income) * 100
                for cat, amt in income_by_cat.items()
            }

        if total_expense > 0:
            expense_pct = {
                cat: (amt / total_expense) * 100
                for cat, amt in expense_by_cat.items()
            }

        return {
            "income_by_cat": income_by_cat,
            "expense_by_cat": expense_by_cat,
            "income_pct": income_pct,
            "expense_pct": expense_pct,
        }

    @staticmethod
    def show_balance(
        wallet: Wallet,
        transactions: List[Transaction] = None,
        is_filtered: bool = False,
    ):
        """Display the total balance with income/expense breakdown.

        Args:
            wallet: The wallet to display.
            transactions: Optional list of transactions to calculate from.
                         If None, uses wallet totals.
            is_filtered: Whether the data is filtered (affects label).
        """
        if transactions is not None:
            totals = Display._calculate_totals(transactions)
            balance = totals["balance"]
            total_income = totals["total_income"]
            total_expense = totals["total_expense"]
        else:
            balance = wallet.balance
            total_income = wallet.total_income
            total_expense = wallet.total_expense

        sign = "+" if balance >= 0 else ""
        label = "Period Balance" if is_filtered else "Balance"
        print(f"\n💰 {label}: {sign}{balance:.2f} {wallet.currency}")
        print(f"   Income:  +{total_income:.2f}")
        print(f"   Expense: -{total_expense:.2f}")

        # Show overall wallet balance when filtered
        if is_filtered:
            overall_sign = "+" if wallet.balance >= 0 else ""
            print(f"   (Overall: {overall_sign}{wallet.balance:.2f})")

    @staticmethod
    def show_category_breakdown(
        wallet: Wallet,
        transactions: List[Transaction] = None,
    ):
        """Display category contributions for income and expenses separately.

        Args:
            wallet: The wallet (used for context).
            transactions: Optional list of transactions to calculate from.
                         If None, uses wallet methods.
        """
        if transactions is not None:
            breakdown = Display._calculate_category_breakdown(transactions)
            income_by_cat = breakdown["income_by_cat"]
            expense_by_cat = breakdown["expense_by_cat"]
            income_pct = breakdown["income_pct"]
            expense_pct = breakdown["expense_pct"]
        else:
            income_by_cat = wallet.get_income_by_category()
            expense_by_cat = wallet.get_expense_by_category()
            income_pct = wallet.get_income_percentages()
            expense_pct = wallet.get_expense_percentages()

        if not income_by_cat and not expense_by_cat:
            print("\n📊 No transactions yet")
            return

        # Show income breakdown
        if income_by_cat:
            print("\n📈 Income by Category:")
            for category, amount in sorted(income_by_cat.items(), key=lambda x: -x[1]):
                pct = income_pct.get(category, 0)
                print(f"   {category}: +{amount:.2f} ({pct:.1f}%)")

        # Show expense breakdown
        if expense_by_cat:
            print("\n📉 Expenses by Category:")
            for category, amount in sorted(expense_by_cat.items(), key=lambda x: -x[1]):
                pct = expense_pct.get(category, 0)
                print(f"   {category}: -{amount:.2f} ({pct:.1f}%)")
    
    @staticmethod
    def show_transactions(wallet: Wallet, use_filter: bool = True):
        """Display transactions (filtered and sorted).

        Args:
            wallet: The wallet to display transactions from.
            use_filter: If True, apply active filters. If False, show all.
        """
        filtering_ctx = wallet.filtering_context
        has_filters = filtering_ctx.has_filters and use_filter

        if has_filters:
            transactions = wallet.get_filtered_transactions()
        else:
            transactions = wallet.get_sorted_transactions()

        strategy_name = wallet.sorting_context.current_strategy.name
        total_count = wallet.transaction_count()

        # Build header
        header = f"\n📋 Transactions (Sorted by: {strategy_name})"
        if has_filters:
            header += f" [Filtered: {len(transactions)}/{total_count}]"
        print(header + ":")

        # Show active filters
        if has_filters:
            print(f"   🔍 Filters: {filtering_ctx.filter_summary}")

        if not transactions:
            if has_filters:
                print("   No transactions match current filters")
            else:
                print("   No transactions")
            return

        for i, t in enumerate(transactions, 1):
            rec_marker = " (R)" if getattr(t, "recurrence_id", None) else ""
            print(f"   {i}. {t}{rec_marker}")
    
    @staticmethod
    def show_transaction_detail(transaction: Transaction):
        """Display detailed transaction information."""
        Display.show_header("Transaction Details")
        print(transaction.detailed_str())
    
    @staticmethod
    def show_dashboard(wallet: Wallet):
        """Display the main dashboard."""
        filtering_ctx = wallet.filtering_context
        has_filters = filtering_ctx.has_filters

        # Get transactions (filtered or all)
        if has_filters:
            transactions = wallet.get_filtered_transactions()
            header = f"Budget Planner Dashboard - {wallet.name} [FILTERED]"
        else:
            transactions = wallet.get_sorted_transactions()
            header = f"Budget Planner Dashboard - {wallet.name}"

        Display.show_header(header)

        # Show active filters summary at top if filtering
        if has_filters:
            print(f"🔍 Active Filters: {filtering_ctx.filter_summary}")
            print(f"   Showing {len(transactions)} of {wallet.transaction_count()} transactions")

        # Show balance and category breakdown from filtered transactions
        Display.show_balance(wallet, transactions if has_filters else None, has_filters)
        Display.show_category_breakdown(wallet, transactions if has_filters else None)
        Display.show_transactions(wallet)
    
    @staticmethod
    def show_help():
        """Display available commands."""
        print("\n📌 Available Commands:")
        print("+--------- Transaction Commands ---------+")
        print("   +          - Add income transaction")
        print("   -          - Add expense transaction")
        print("   transfer   - Transfer money between wallets")
        print("   show <N>   - Show details of transaction N")
        print("   edit <N>   - Edit transaction N")
        print("   delete <N> - Delete transaction N")
        print("   sort       - Change sorting method")
        print("   filter     - Filter transactions")
        print("   percent    - Show category percentages")
        print("+----------- Wallet Commands ------------+")
        print("   wallets              - Show all wallets")
        print("   add_wallet           - Add a new wallet")
        print("   wallet <name>        - Show wallet details")
        print("   edit_wallet <name>   - Edit a wallet")
        print("   delete_wallet <name> - Delete a wallet")
        print("   switch <name>        - Switch to a wallet")
        print("   sort_wallets         - Change wallet sorting")
        print("+-------- Recurring Commands ------------+")
        print("   +r              - Add recurring income")
        print("   -r              - Add recurring expense")
        print("   recurring       - List recurring transactions")
        print("   show_rec <N>    - Show recurring details")
        print("   edit_rec <N>    - Edit recurring transaction")
        print("   delete_rec <N>  - Delete recurring transaction")
        print("+----------- General Commands -----------+")
        print("   home       - Show dashboard")
        print("   help       - Show this help message")
        print("   quit       - Exit the program")
    
    @staticmethod
    def show_categories(categories, transaction_type_name: str):
        """Display available categories."""
        print(f"\n📁 Available {transaction_type_name} Categories:")
        for i, cat in enumerate(sorted(categories), 1):
            print(f"   {i}. {cat}")
        print(f"   {len(categories) + 1}. [Add new category]")
    
    @staticmethod
    def show_sorting_options():
        """Display available sorting options."""
        strategies = SortingContext.get_available_strategies()
        print("\n🔄 Sorting Options:")
        for key, name in strategies.items():
            print(f"   {key}. {name}")
    
    @staticmethod
    def show_success(message: str):
        """Display a success message."""
        print(f"\n✅ {message}")
    
    @staticmethod
    def show_error(message: str):
        """Display an error message."""
        print(f"\n❌ {message}")
    
    @staticmethod
    def show_info(message: str):
        """Display an info message."""
        print(f"\nℹ️  {message}")

    @staticmethod
    def show_wallets(wallet_manager: "WalletManager"):
        """Display all wallets in sorted order."""
        wallets = wallet_manager.get_sorted_wallets()
        strategy_name = wallet_manager.sorting_context.current_strategy.name
        current = wallet_manager.current_wallet

        print(f"\n💼 Wallets (Sorted by: {strategy_name}):")

        if not wallets:
            print("   No wallets")
            return

        for i, w in enumerate(wallets, 1):
            marker = " *" if current and w.name == current.name else ""
            sign = "+" if w.balance >= 0 else ""
            wallet_type_tag = f"[{w.wallet_type.value[0].upper()}]"
            print(
                f"   {i}. {wallet_type_tag} {w.name} ({w.currency}) - "
                f"{sign}{w.balance:.2f}{marker}"
            )

        if current:
            print(f"\n   * Current wallet: {current.name}")
        print("\n   [R] = Regular, [D] = Deposit")

    @staticmethod
    def show_wallet_detail(wallet: Wallet):
        """Display detailed wallet information."""
        wallet_type_label = wallet.wallet_type.value.capitalize()
        Display.show_header(f"{wallet_type_label} Wallet: {wallet.name}")
        print(f"   ID:          {wallet.id}")
        print(f"   Type:        {wallet_type_label}")
        print(f"   Name:        {wallet.name}")
        print(f"   Currency:    {wallet.currency}")
        print(f"   Description: {wallet.description or 'N/A'}")
        print(f"   Created:     {wallet.datetime_created.strftime('%Y-%m-%d %H:%M')}")
        print(f"   Balance:     {'+' if wallet.balance >= 0 else ''}{wallet.balance:.2f}")
        print(f"   Income:      +{wallet.total_income:.2f}")
        print(f"   Expense:     -{wallet.total_expense:.2f}")
        print(f"   Transactions: {wallet.transaction_count()}")

        # Show deposit-specific information
        if isinstance(wallet, DepositWallet):
            Display.show_deposit_details(wallet)

    @staticmethod
    def show_deposit_details(wallet: DepositWallet):
        """Display deposit-specific details."""
        print("\n   --- Deposit Details ---")
        print(f"   Interest Rate:    {wallet.interest_rate:.2f}% per year")
        print(f"   Term:             {wallet.term_months} months")
        print(f"   Capitalization:   {'Yes' if wallet.capitalization else 'No'}")
        print(f"   Maturity Date:    {wallet.maturity_date.strftime('%Y-%m-%d')}")

        if wallet.is_matured:
            print("   Status:           MATURED")
        else:
            print(f"   Days to Maturity: {wallet.days_until_maturity} days")

        print(f"\n   Principal:        {wallet.principal:.2f} {wallet.currency}")
        print(f"   Accrued Interest: {wallet.calculate_accrued_interest():.2f} {wallet.currency}")
        print(f"   Total at Maturity: {wallet.calculate_maturity_amount():.2f} {wallet.currency}")

    @staticmethod
    def show_wallet_sorting_options():
        """Display available wallet sorting options."""
        strategies = WalletSortingContext.get_available_strategies()
        print("\n🔄 Wallet Sorting Options:")
        for key, name in strategies.items():
            print(f"   {key}. {name}")

    @staticmethod
    def show_filter_menu():
        """Display the filter menu options."""
        print("\n🔍 Filter Options:")
        print("   1. Filter by Date")
        print("   2. Filter by Transaction Type")
        print("   3. Filter by Category")
        print("   4. Filter by Amount")
        print("   5. Filter by Description")
        print("   6. View Active Filters")
        print("   7. Remove a Filter")
        print("   8. Clear All Filters")
        print("   0. Back / Cancel")

    @staticmethod
    def show_date_filter_options():
        """Display date filter presets."""
        presets = FilteringContext.get_date_presets()
        print("\n📅 Date Filter Options:")
        for key, name in presets.items():
            print(f"   {key}. {name}")
        print("   0. Cancel")

    @staticmethod
    def show_type_filter_options():
        """Display transaction type filter options."""
        presets = FilteringContext.get_type_presets()
        print("\n📊 Transaction Type Filter Options:")
        for key, name in presets.items():
            print(f"   {key}. {name}")
        print("   0. Cancel")

    @staticmethod
    def show_amount_filter_options():
        """Display amount filter presets."""
        presets = FilteringContext.get_amount_presets()
        print("\n💵 Amount Filter Options:")
        for key, name in presets.items():
            print(f"   {key}. {name}")
        print("   0. Cancel")

    @staticmethod
    def show_active_filters(wallet: Wallet):
        """Display currently active filters."""
        filters = wallet.filtering_context.active_filters
        print("\n🔍 Active Filters:")
        if not filters:
            print("   No filters active")
            return
        for i, f in enumerate(filters, 1):
            print(f"   {i}. {f.name}: {f.description}")

    @staticmethod
    def show_recurring_transactions(recurring_list: List["RecurringTransaction"]):
        """Display a list of recurring transactions."""
        Display.show_header("Recurring Transactions")
        if not recurring_list:
            print("   No recurring transactions")
            return

        for i, r in enumerate(recurring_list, 1):
            print(f"   {i}. {r.summary_str()}")

    @staticmethod
    def show_recurring_detail(recurring: "RecurringTransaction"):
        """Display detailed recurring transaction information."""
        Display.show_header("Recurring Transaction Details")
        print(recurring.detailed_str())
