"""Display utilities for the budget planner."""
from typing import List, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from wallet.wallet_manager import WalletManager
from models.transaction import Transaction
from wallet.wallet import Wallet, DepositWallet, WalletType
from strategies.sorting import SortingContext, WalletSortingContext


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
    def show_balance(wallet: Wallet):
        """Display the total balance with income/expense breakdown."""
        balance = wallet.balance
        sign = "+" if balance >= 0 else ""
        print(f"\n💰 Balance: {sign}{balance:.2f} {wallet.currency}")
        print(f"   Income:  +{wallet.total_income:.2f}")
        print(f"   Expense: -{wallet.total_expense:.2f}")

    @staticmethod
    def show_category_breakdown(wallet: Wallet):
        """Display category contributions for income and expenses separately."""
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
    def show_transactions(wallet: Wallet):
        """Display all transactions in sorted order."""
        transactions = wallet.get_sorted_transactions()
        strategy_name = wallet.sorting_context.current_strategy.name
        
        print(f"\n📋 Transactions (Sorted by: {strategy_name}):")
        
        if not transactions:
            print("   No transactions")
            return
        
        for i, t in enumerate(transactions, 1):
            print(f"   {i}. {t}")
    
    @staticmethod
    def show_transaction_detail(transaction: Transaction):
        """Display detailed transaction information."""
        Display.show_header("Transaction Details")
        print(transaction.detailed_str())
    
    @staticmethod
    def show_dashboard(wallet: Wallet):
        """Display the main dashboard."""
        Display.show_header(f"Budget Planner Dashboard - {wallet.name}")
        Display.show_balance(wallet)
        Display.show_category_breakdown(wallet)
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
        print("   percent    - Show category percentages")
        print("+----------- Wallet Commands ------------+")
        print("   wallets              - Show all wallets")
        print("   add_wallet           - Add a new wallet")
        print("   wallet <name>        - Show wallet details")
        print("   edit_wallet <name>   - Edit a wallet")
        print("   delete_wallet <name> - Delete a wallet")
        print("   switch <name>        - Switch to a wallet")
        print("   sort_wallets         - Change wallet sorting")
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
