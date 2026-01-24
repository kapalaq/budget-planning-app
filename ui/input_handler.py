"""Input handling utilities for the budget planner."""
from datetime import datetime
from typing import Optional, Tuple, Set, Dict, List, TYPE_CHECKING
from models.transaction import Transaction, TransactionType
from ui.display import Display
from wallet.wallet import Wallet, WalletType

if TYPE_CHECKING:
    from wallet.wallet_manager import WalletManager


class InputHandler:
    """Handles all user input operations."""
    
    @staticmethod
    def get_command() -> str:
        """Get a command from user."""
        return input("\n> ").strip().lower()
    
    @staticmethod
    def get_amount() -> Optional[float]:
        """Get a valid amount from user."""
        try:
            amount_str = input("Enter amount: ").strip()
            amount = float(amount_str)
            if amount <= 0:
                Display.show_error("Amount must be positive")
                return None
            return amount
        except ValueError:
            Display.show_error("Invalid amount. Please enter a number.")
            return None
    
    @staticmethod
    def get_category(categories: Set[str], transaction_type: TransactionType) -> Optional[str]:
        """Get a category from user, with option to add new."""
        type_name = "Income" if transaction_type == TransactionType.INCOME else "Expense"
        Display.show_categories(categories, type_name)
        
        sorted_categories = sorted(categories)
        choice = input("Select category (number or name): ").strip()
        
        # Check if it's a number
        try:
            choice_num = int(choice)
            if 1 <= choice_num <= len(sorted_categories):
                return sorted_categories[choice_num - 1]
            elif choice_num == len(sorted_categories) + 1:
                # Add new category
                new_category = input("Enter new category name: ").strip()
                if new_category:
                    return new_category
                Display.show_error("Category name cannot be empty")
                return None
            else:
                Display.show_error("Invalid selection")
                return None
        except ValueError:
            # It's a name - check if it exists or add it
            if choice in categories:
                return choice
            # Ask if they want to add it
            confirm = input(f"Category '{choice}' doesn't exist. Add it? (y/n): ").strip().lower()
            if confirm == 'y':
                return choice
            return None
    
    @staticmethod
    def get_description() -> str:
        """Get an optional description from user."""
        return input("Enter description (optional): ").strip()
    
    @staticmethod
    def get_datetime() -> datetime:
        """Get datetime from user, defaulting to now."""
        date_str = input("Enter date (YYYY-MM-DD) or press Enter for today: ").strip()
        
        if not date_str:
            return datetime.now()
        
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            Display.show_info("Invalid date format. Using current date.")
            return datetime.now()
    
    @staticmethod
    def get_transaction_input(
        transaction_type: TransactionType,
        categories: Set[str]
    ) -> Optional[Transaction]:
        """Get all inputs for a new transaction step by step."""
        type_name = "Income" if transaction_type == TransactionType.INCOME else "Expense"
        Display.show_header(f"New {type_name} Transaction")
        
        # Step 1: Amount
        amount = InputHandler.get_amount()
        if amount is None:
            return None
        
        # Step 2: Category
        category = InputHandler.get_category(categories, transaction_type)
        if category is None:
            return None
        
        # Step 3: Description
        description = InputHandler.get_description()
        
        # Step 4: Date
        date = InputHandler.get_datetime()
        
        return Transaction(
            amount=amount,
            transaction_type=transaction_type,
            category=category,
            description=description,
            datetime_created=date
        )
    
    @staticmethod
    def get_edit_input(
        transaction: Transaction,
        categories: Set[str]
    ) -> Optional[Transaction]:
        """Get inputs for editing a transaction."""
        Display.show_header("Edit Transaction")
        Display.show_info("Press Enter to keep current value")
        
        print(f"\nCurrent values:")
        print(transaction.detailed_str())
        print()
        
        # Amount
        amount_str = input(f"Amount [{transaction.amount}]: ").strip()
        if amount_str:
            try:
                amount = float(amount_str)
                if amount <= 0:
                    Display.show_error("Amount must be positive")
                    return None
            except ValueError:
                Display.show_error("Invalid amount")
                return None
        else:
            amount = transaction.amount
        
        # Category
        print(f"\nCurrent category: {transaction.category}")
        change_cat = input("Change category? (y/n): ").strip().lower()
        if change_cat == 'y':
            category = InputHandler.get_category(categories, transaction.transaction_type)
            if category is None:
                return None
        else:
            category = transaction.category
        
        # Description
        desc_input = input(f"Description [{transaction.description or 'N/A'}]: ").strip()
        description = desc_input if desc_input else transaction.description
        
        # Date
        current_date = transaction.datetime_created.strftime("%Y-%m-%d")
        date_str = input(f"Date [{current_date}]: ").strip()
        if date_str:
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                Display.show_info("Invalid date format. Keeping current date.")
                date = transaction.datetime_created
        else:
            date = transaction.datetime_created
        
        return Transaction(
            amount=amount,
            transaction_type=transaction.transaction_type,
            category=category,
            description=description,
            datetime_created=date
        )
    
    @staticmethod
    def confirm(message: str) -> bool:
        """Get a yes/no confirmation from user."""
        response = input(f"{message} (y/n): ").strip().lower()
        return response == 'y'
    
    @staticmethod
    def parse_indexed_command(command: str) -> Tuple[Optional[str], Optional[int]]:
        """Parse commands like 'show 1', 'edit 2', 'delete 3'."""
        parts = command.split()
        if len(parts) != 2:
            return None, None

        action = parts[0]
        try:
            index = int(parts[1])
            return action, index
        except ValueError:
            return None, None

    @staticmethod
    def parse_named_command(command: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse commands like 'wallet Main', 'switch Savings'."""
        parts = command.split(maxsplit=1)
        if len(parts) != 2:
            return None, None
        return parts[0], parts[1]

    @staticmethod
    def get_wallet_type() -> Optional[WalletType]:
        """Get wallet type from user."""
        print("\n📁 Wallet Types:")
        print("   1. Regular - Standard wallet for daily transactions")
        print("   2. Deposit - Savings with interest rate and maturity date")

        choice = input("Select wallet type (1/2): ").strip()

        if choice == "1":
            return WalletType.REGULAR
        elif choice == "2":
            return WalletType.DEPOSIT
        else:
            Display.show_error("Invalid selection")
            return None

    @staticmethod
    def get_wallet_input() -> Optional[Dict]:
        """Get all inputs for a new wallet step by step."""
        Display.show_header("New Wallet")

        # Step 1: Wallet type
        wallet_type = InputHandler.get_wallet_type()
        if wallet_type is None:
            return None

        # Step 2: Name (required)
        name = input("Enter wallet name: ").strip()
        if not name:
            Display.show_error("Wallet name cannot be empty")
            return None

        # Step 3: Currency
        currency = input("Enter currency (default: KZT): ").strip()
        if not currency:
            currency = "KZT"

        # Step 4: Starting balance
        starting_str = input("Enter starting balance (default: 0): ").strip()
        starting_value = None
        if starting_str:
            try:
                starting_value = float(starting_str)
            except ValueError:
                Display.show_info("Invalid amount. Starting with 0.")

        # Step 5: Description
        description = input("Enter description (optional): ").strip()

        result = {
            "name": name,
            "currency": currency,
            "starting_value": starting_value,
            "description": description,
            "wallet_type": wallet_type,
        }

        # Step 6: Deposit-specific inputs
        if wallet_type == WalletType.DEPOSIT:
            deposit_data = InputHandler.get_deposit_input()
            if deposit_data is None:
                return None
            result.update(deposit_data)

        return result

    @staticmethod
    def get_deposit_input() -> Optional[Dict]:
        """Get deposit-specific inputs."""
        print("\n--- Deposit Settings ---")

        # Interest rate
        rate_str = input("Enter annual interest rate (e.g., 12.5 for 12.5%): ").strip()
        try:
            interest_rate = float(rate_str)
            if interest_rate <= 0:
                Display.show_error("Interest rate must be positive")
                return None
        except ValueError:
            Display.show_error("Invalid interest rate")
            return None

        # Term in months
        term_str = input("Enter term in months: ").strip()
        try:
            term_months = int(term_str)
            if term_months <= 0:
                Display.show_error("Term must be positive")
                return None
        except ValueError:
            Display.show_error("Invalid term")
            return None

        # Capitalization
        cap_choice = input("Enable interest capitalization? (y/n, default: n): ").strip().lower()
        capitalization = cap_choice == 'y'

        return {
            "interest_rate": interest_rate,
            "term_months": term_months,
            "capitalization": capitalization,
        }

    @staticmethod
    def get_wallet_edit_input(wallet: Wallet) -> Optional[Dict]:
        """Get inputs for editing a wallet."""
        Display.show_header("Edit Wallet")
        Display.show_info("Press Enter to keep current value")

        print(f"\nCurrent values:")
        print(f"   Name:        {wallet.name}")
        print(f"   Currency:    {wallet.currency}")
        print(f"   Description: {wallet.description or 'N/A'}")
        print()

        # Name
        new_name = input(f"Name [{wallet.name}]: ").strip()
        if not new_name:
            new_name = wallet.name

        # Currency
        new_currency = input(f"Currency [{wallet.currency}]: ").strip()
        if not new_currency:
            new_currency = wallet.currency

        # Description
        new_desc = input(f"Description [{wallet.description or 'N/A'}]: ").strip()
        if not new_desc:
            new_desc = wallet.description

        return {
            "new_name": new_name if new_name != wallet.name else None,
            "currency": new_currency if new_currency != wallet.currency else None,
            "description": new_desc,
        }

    @staticmethod
    def get_transfer_input(
        current_wallet: Wallet,
        available_wallets: List[Wallet]
    ) -> Optional[Dict]:
        """Get all inputs for a new transfer.

        Args:
            current_wallet: The wallet from which money is being transferred.
            available_wallets: List of all available wallets (excluding current).

        Returns:
            Dictionary with transfer details or None if cancelled.
        """
        Display.show_header("New Transfer")

        # Filter out current wallet from available options
        target_wallets = [w for w in available_wallets if w.name != current_wallet.name]

        if not target_wallets:
            Display.show_error("No other wallets available for transfer. Create another wallet first.")
            return None

        # Step 1: Select target wallet
        print(f"\nTransferring FROM: {current_wallet.name} ({current_wallet.currency})")
        print(f"Available balance: {current_wallet.balance:.2f}")
        print("\nSelect target wallet:")
        for i, wallet in enumerate(target_wallets, 1):
            print(f"   {i}. {wallet.name} ({wallet.currency}) - Balance: {wallet.balance:.2f}")

        choice = input("\nSelect wallet (number): ").strip()
        try:
            choice_num = int(choice)
            if 1 <= choice_num <= len(target_wallets):
                target_wallet = target_wallets[choice_num - 1]
            else:
                Display.show_error("Invalid selection")
                return None
        except ValueError:
            Display.show_error("Invalid selection")
            return None

        # Step 2: Amount
        amount = InputHandler.get_amount()
        if amount is None:
            return None

        # Step 3: Description
        description = InputHandler.get_description()

        # Step 4: Date
        date = InputHandler.get_datetime()

        return {
            "target_wallet_name": target_wallet.name,
            "amount": amount,
            "description": description,
            "datetime_created": date,
        }

    @staticmethod
    def get_transfer_edit_input(transfer: "Transaction") -> Optional[Dict]:
        """Get inputs for editing a transfer transaction.

        Note: For transfers, only amount, description, and date can be edited.
        The category remains 'Transfer' and wallets cannot be changed.
        """
        Display.show_header("Edit Transfer")
        Display.show_info("Press Enter to keep current value")
        Display.show_info("Note: Transfer category and wallets cannot be changed")

        print(f"\nCurrent values:")
        print(transfer.detailed_str())
        print()

        # Amount
        amount_str = input(f"Amount [{transfer.amount}]: ").strip()
        if amount_str:
            try:
                amount = float(amount_str)
                if amount <= 0:
                    Display.show_error("Amount must be positive")
                    return None
            except ValueError:
                Display.show_error("Invalid amount")
                return None
        else:
            amount = transfer.amount

        # Description
        desc_input = input(f"Description [{transfer.description or 'N/A'}]: ").strip()
        description = desc_input if desc_input else transfer.description

        # Date
        current_date = transfer.datetime_created.strftime("%Y-%m-%d")
        date_str = input(f"Date [{current_date}]: ").strip()
        if date_str:
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                Display.show_info("Invalid date format. Keeping current date.")
                date = transfer.datetime_created
        else:
            date = transfer.datetime_created

        return {
            "amount": amount,
            "description": description,
            "datetime_created": date,
        }
