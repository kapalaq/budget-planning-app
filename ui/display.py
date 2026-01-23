"""Display utilities for the budget planner."""
from typing import List, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from wallet.wallet_manager import WalletManager
from models.transaction import Transaction
from wallet.wallet import Wallet
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
        """Display the total balance."""
        balance = wallet.balance
        sign = "+" if balance >= 0 else ""
        print(f"\n💰 Total Balance: {sign}{balance:.2f}")
    
    @staticmethod
    def show_category_breakdown(wallet: Wallet):
        """Display category contributions."""
        totals = wallet.get_category_totals()
        percentages = wallet.get_category_percentages()
        
        if not totals:
            print("\n📊 No transactions yet")
            return
        
        print("\n📊 Category Breakdown:")
        for category, total in sorted(totals.items()):
            pct = percentages.get(category, 0)
            sign = "+" if total >= 0 else ""
            print(f"   {category}: {sign}{total:.2f} ({pct:.1f}%)")
    
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
            print(
                f"   {i}. {w.name} ({w.currency}) - {sign}{w.balance:.2f}{marker}"
            )

        if current:
            print(f"\n   * Current wallet: {current.name}")

    @staticmethod
    def show_wallet_detail(wallet: Wallet):
        """Display detailed wallet information."""
        Display.show_header(f"Wallet: {wallet.name}")
        print(f"   ID:          {wallet.id}")
        print(f"   Name:        {wallet.name}")
        print(f"   Currency:    {wallet.currency}")
        print(f"   Description: {wallet.description or 'N/A'}")
        print(f"   Created:     {wallet.datetime_created.strftime('%Y-%m-%d %H:%M')}")
        print(f"   Balance:     {'+' if wallet.balance >= 0 else ''}{wallet.balance:.2f}")
        print(f"   Income:      +{wallet.total_income:.2f}")
        print(f"   Expense:     -{wallet.total_expense:.2f}")
        print(f"   Transactions: {wallet.transaction_count()}")

    @staticmethod
    def show_wallet_sorting_options():
        """Display available wallet sorting options."""
        strategies = WalletSortingContext.get_available_strategies()
        print("\n🔄 Wallet Sorting Options:")
        for key, name in strategies.items():
            print(f"   {key}. {name}")
