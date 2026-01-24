"""Command handlers for the budget planner using Command Pattern."""
from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from wallet.wallet_manager import WalletManager
from wallet.wallet import Wallet, DepositWallet, WalletType
from models.transaction import Transaction, Transfer, TransactionType
from ui.display import Display
from ui.input_handler import InputHandler


class Command(ABC):
    """Abstract base class for commands."""
    
    @abstractmethod
    def execute(self) -> bool:
        """Execute the command. Returns True if app should continue."""
        pass


class AddTransactionCommand(Command):
    """Command to add a new transaction."""

    def __init__(
        self, wallet_manager: "WalletManager", transaction_type: TransactionType
    ):
        self._wallet_manager = wallet_manager
        self._transaction_type = transaction_type

    def execute(self) -> bool:
        wallet = self._wallet_manager.current_wallet
        if not wallet:
            Display.show_error("No wallet selected. Create or switch to a wallet first.")
            return True

        categories = wallet.category_manager.get_categories(self._transaction_type)
        transaction = InputHandler.get_transaction_input(
            self._transaction_type, categories
        )

        if transaction:
            wallet.add_transaction(transaction)
            Display.show_success("Transaction added successfully!")
        else:
            Display.show_error("Transaction cancelled")

        return True


class ShowTransactionCommand(Command):
    """Command to show transaction details."""

    def __init__(self, wallet_manager: "WalletManager", index: int):
        self._wallet_manager = wallet_manager
        self._index = index

    def execute(self) -> bool:
        wallet = self._wallet_manager.current_wallet
        if not wallet:
            Display.show_error("No wallet selected.")
            return True

        transaction = wallet.get_transaction(self._index)

        if transaction:
            Display.show_transaction_detail(transaction)
        else:
            Display.show_error(f"Transaction #{self._index} not found")

        return True


class EditTransactionCommand(Command):
    """Command to edit a transaction."""

    def __init__(self, wallet_manager: "WalletManager", index: int):
        self._wallet_manager = wallet_manager
        self._index = index

    def execute(self) -> bool:
        wallet = self._wallet_manager.current_wallet
        if not wallet:
            Display.show_error("No wallet selected.")
            return True

        transaction = wallet.get_transaction(self._index)

        if not transaction:
            Display.show_error(f"Transaction #{self._index} not found")
            return True

        # Handle transfer edits differently
        if isinstance(transaction, Transfer):
            edit_data = InputHandler.get_transfer_edit_input(transaction)
            if edit_data:
                # Create a simple Transaction object with the updated values
                updated = Transaction(
                    amount=edit_data["amount"],
                    transaction_type=transaction.transaction_type,
                    category="Transfer",
                    description=edit_data["description"],
                    datetime_created=edit_data["datetime_created"],
                )
                if wallet.update_transaction(self._index, updated):
                    Display.show_success(
                        "Transfer updated successfully! "
                        "(Both wallets have been synchronized)"
                    )
                else:
                    Display.show_error("Failed to update transfer")
            else:
                Display.show_info("Edit cancelled")
        else:
            # Regular transaction edit
            categories = wallet.category_manager.get_categories(transaction.transaction_type)
            updated = InputHandler.get_edit_input(transaction, categories)

            if updated:
                if wallet.update_transaction(self._index, updated):
                    Display.show_success("Transaction updated successfully!")
                else:
                    Display.show_error("Failed to update transaction")
            else:
                Display.show_info("Edit cancelled")

        return True


class DeleteTransactionCommand(Command):
    """Command to delete a transaction."""

    def __init__(self, wallet_manager: "WalletManager", index: int):
        self._wallet_manager = wallet_manager
        self._index = index

    def execute(self) -> bool:
        wallet = self._wallet_manager.current_wallet
        if not wallet:
            Display.show_error("No wallet selected.")
            return True

        transaction = wallet.get_transaction(self._index)

        if not transaction:
            Display.show_error(f"Transaction #{self._index} not found")
            return True

        Display.show_transaction_detail(transaction)

        # Show additional warning for transfers
        if isinstance(transaction, Transfer):
            Display.show_info(
                "This is a transfer. Deleting it will also remove "
                "the corresponding transaction from the other wallet."
            )

        if InputHandler.confirm("Are you sure you want to delete this transaction?"):
            if wallet.delete_transaction(self._index):
                Display.show_success("Transaction deleted successfully!")
            else:
                Display.show_error("Failed to delete transaction")
        else:
            Display.show_info("Deletion cancelled")

        return True


class TransferCommand(Command):
    """Command to transfer money between wallets."""

    def __init__(self, wallet_manager: "WalletManager"):
        self._wallet_manager = wallet_manager

    def execute(self) -> bool:
        wallet = self._wallet_manager.current_wallet
        if not wallet:
            Display.show_error("No wallet selected. Create or switch to a wallet first.")
            return True

        if self._wallet_manager.wallet_count() < 2:
            Display.show_error("You need at least two wallets to make a transfer.")
            return True

        # Get all wallets for selection
        available_wallets = self._wallet_manager.get_sorted_wallets()

        transfer_data = InputHandler.get_transfer_input(wallet, available_wallets)

        if transfer_data:
            if self._wallet_manager.transfer(
                from_wallet_name=wallet.name,
                to_wallet_name=transfer_data["target_wallet_name"],
                amount=transfer_data["amount"],
                description=transfer_data["description"],
                datetime_created=transfer_data["datetime_created"],
            ):
                Display.show_success(
                    f"Transferred {transfer_data['amount']:.2f} from "
                    f"'{wallet.name}' to '{transfer_data['target_wallet_name']}'!"
                )
            else:
                Display.show_error("Failed to complete transfer")
        else:
            Display.show_info("Transfer cancelled")

        return True


class ChangeSortingCommand(Command):
    """Command to change transaction sorting strategy."""

    def __init__(self, wallet_manager: "WalletManager"):
        self._wallet_manager = wallet_manager

    def execute(self) -> bool:
        wallet = self._wallet_manager.current_wallet
        if not wallet:
            Display.show_error("No wallet selected.")
            return True

        Display.show_sorting_options()
        choice = input("Select sorting method: ").strip()

        if wallet.sorting_context.set_strategy(choice):
            Display.show_success(
                f"Sorting changed to: {wallet.sorting_context.current_strategy.name}"
            )
        else:
            Display.show_error("Invalid sorting option")

        return True


class ShowPercentagesCommand(Command):
    """Command to show category percentages."""

    def __init__(self, wallet_manager: "WalletManager"):
        self._wallet_manager = wallet_manager

    def execute(self) -> bool:
        wallet = self._wallet_manager.current_wallet
        if not wallet:
            Display.show_error("No wallet selected.")
            return True

        income_pct = wallet.get_income_percentages()
        expense_pct = wallet.get_expense_percentages()

        if not income_pct and not expense_pct:
            Display.show_info("No transactions to calculate percentages")
            return True

        Display.show_header("Category Percentages")

        if income_pct:
            print("\n📈 Income:")
            for category, pct in sorted(income_pct.items(), key=lambda x: -x[1]):
                print(f"   {category}: {pct:.1f}%")

        if expense_pct:
            print("\n📉 Expenses:")
            for category, pct in sorted(expense_pct.items(), key=lambda x: -x[1]):
                print(f"   {category}: {pct:.1f}%")

        return True


class HelpCommand(Command):
    """Command to show help."""
    
    def execute(self) -> bool:
        Display.show_help()
        return True


class QuitCommand(Command):
    """Command to quit the application."""
    
    def execute(self) -> bool:
        Display.show_info("Thank you for using Budget Planner. Goodbye!")
        return False


class RefreshCommand(Command):
    """Command to refresh/show dashboard."""

    def __init__(self, wallet_manager: "WalletManager"):
        self._wallet_manager = wallet_manager

    def execute(self) -> bool:
        wallet = self._wallet_manager.current_wallet
        if wallet:
            Display.show_dashboard(wallet)
        else:
            Display.show_info("No wallet selected. Create or switch to a wallet first.")
        return True


# ============= Wallet Commands =============


class ShowWalletsCommand(Command):
    """Command to show all wallets."""

    def __init__(self, wallet_manager: "WalletManager"):
        self._wallet_manager = wallet_manager

    def execute(self) -> bool:
        Display.show_wallets(self._wallet_manager)
        return True


class ShowWalletCommand(Command):
    """Command to show a specific wallet's details."""

    def __init__(self, wallet_manager: "WalletManager", name: str):
        self._wallet_manager = wallet_manager
        self._name = name

    def execute(self) -> bool:
        wallet = self._wallet_manager.get_wallet(self._name)
        if wallet:
            Display.show_wallet_detail(wallet)
        else:
            Display.show_error(f"Wallet '{self._name}' not found")
        return True


class AddWalletCommand(Command):
    """Command to add a new wallet."""

    def __init__(self, wallet_manager: "WalletManager"):
        self._wallet_manager = wallet_manager

    def execute(self) -> bool:
        wallet_data = InputHandler.get_wallet_input()

        if wallet_data:
            wallet_type = wallet_data.get("wallet_type", WalletType.REGULAR)

            if wallet_type == WalletType.DEPOSIT:
                new_wallet = DepositWallet(
                    name=wallet_data["name"],
                    interest_rate=wallet_data["interest_rate"],
                    term_months=wallet_data["term_months"],
                    starting_value=wallet_data["starting_value"],
                    currency=wallet_data["currency"],
                    description=wallet_data["description"],
                    capitalization=wallet_data.get("capitalization", False),
                )
            else:
                new_wallet = Wallet(
                    name=wallet_data["name"],
                    starting_value=wallet_data["starting_value"],
                    currency=wallet_data["currency"],
                    description=wallet_data["description"],
                )

            if self._wallet_manager.add_wallet(new_wallet):
                Display.show_success(f"Wallet '{new_wallet.name}' created successfully!")
            else:
                Display.show_error(
                    f"Wallet with name '{wallet_data['name']}' already exists"
                )
        else:
            Display.show_error("Wallet creation cancelled")

        return True


class EditWalletCommand(Command):
    """Command to edit a wallet."""

    def __init__(self, wallet_manager: "WalletManager", name: str):
        self._wallet_manager = wallet_manager
        self._name = name

    def execute(self) -> bool:
        wallet = self._wallet_manager.get_wallet(self._name)
        if not wallet:
            Display.show_error(f"Wallet '{self._name}' not found")
            return True

        edit_data = InputHandler.get_wallet_edit_input(wallet)

        if edit_data:
            if self._wallet_manager.update_wallet(
                old_name=self._name,
                new_name=edit_data.get("new_name"),
                currency=edit_data.get("currency"),
                description=edit_data.get("description"),
            ):
                Display.show_success("Wallet updated successfully!")
            else:
                Display.show_error(
                    "Failed to update wallet. Name may already be in use."
                )
        else:
            Display.show_error("Edit cancelled")

        return True


class DeleteWalletCommand(Command):
    """Command to delete a wallet."""

    def __init__(self, wallet_manager: "WalletManager", name: str):
        self._wallet_manager = wallet_manager
        self._name = name

    def execute(self) -> bool:
        wallet = self._wallet_manager.get_wallet(self._name)
        if not wallet:
            Display.show_error(f"Wallet '{self._name}' not found")
            return True

        Display.show_wallet_detail(wallet)

        if InputHandler.confirm(
            f"Are you sure you want to delete wallet '{self._name}'?"
        ):
            if self._wallet_manager.remove_wallet(self._name):
                Display.show_success(f"Wallet '{self._name}' deleted successfully!")
            else:
                Display.show_error("Failed to delete wallet")
        else:
            Display.show_info("Deletion cancelled")

        return True


class SwitchWalletCommand(Command):
    """Command to switch to a different wallet."""

    def __init__(self, wallet_manager: "WalletManager", name: str):
        self._wallet_manager = wallet_manager
        self._name = name

    def execute(self) -> bool:
        if self._wallet_manager.switch_wallet(self._name):
            Display.show_success(f"Switched to wallet '{self._name}'")
            Display.show_dashboard(self._wallet_manager.current_wallet)
        else:
            Display.show_error(f"Wallet '{self._name}' not found")
        return True


class ChangeWalletSortingCommand(Command):
    """Command to change wallet sorting strategy."""

    def __init__(self, wallet_manager: "WalletManager"):
        self._wallet_manager = wallet_manager

    def execute(self) -> bool:
        Display.show_wallet_sorting_options()
        choice = input("Select wallet sorting method: ").strip()

        if self._wallet_manager.sorting_context.set_strategy(choice):
            Display.show_success(
                f"Wallet sorting changed to: "
                f"{self._wallet_manager.sorting_context.current_strategy.name}"
            )
        else:
            Display.show_error("Invalid sorting option")

        return True


class CommandFactory:
    """Factory for creating commands."""

    def __init__(self, wallet_manager: "WalletManager"):
        self._wallet_manager = wallet_manager

    def create_command(self, command_str: str) -> Optional[Command]:
        """Create a command based on user input."""
        command_str_lower = command_str.strip().lower()

        # Simple commands
        if command_str_lower == "+":
            return AddTransactionCommand(self._wallet_manager, TransactionType.INCOME)
        elif command_str_lower == "-":
            return AddTransactionCommand(self._wallet_manager, TransactionType.EXPENSE)
        elif command_str_lower == "transfer":
            return TransferCommand(self._wallet_manager)
        elif command_str_lower == "sort":
            return ChangeSortingCommand(self._wallet_manager)
        elif command_str_lower == "percent":
            return ShowPercentagesCommand(self._wallet_manager)
        elif command_str_lower == "help":
            return HelpCommand()
        elif command_str_lower in ("quit", "exit", "q"):
            return QuitCommand()
        elif command_str_lower in ("", "refresh", "home"):
            return RefreshCommand(self._wallet_manager)

        # Wallet commands (simple)
        if command_str_lower == "wallets":
            return ShowWalletsCommand(self._wallet_manager)
        elif command_str_lower == "add_wallet":
            return AddWalletCommand(self._wallet_manager)
        elif command_str_lower == "sort_wallets":
            return ChangeWalletSortingCommand(self._wallet_manager)

        # Transaction indexed commands (show 1, edit 2, delete 3)
        action, index = InputHandler.parse_indexed_command(command_str_lower)
        if action and index:
            if action == "show":
                return ShowTransactionCommand(self._wallet_manager, index)
            elif action == "edit":
                return EditTransactionCommand(self._wallet_manager, index)
            elif action == "delete":
                return DeleteTransactionCommand(self._wallet_manager, index)

        # Wallet named commands (wallet Name, switch Name, etc.)
        # Keep original case for wallet names
        action, name = InputHandler.parse_named_command(command_str)
        if action and name:
            action_lower = action.lower()
            if action_lower == "wallet":
                return ShowWalletCommand(self._wallet_manager, name)
            elif action_lower == "edit_wallet":
                return EditWalletCommand(self._wallet_manager, name)
            elif action_lower == "delete_wallet":
                return DeleteWalletCommand(self._wallet_manager, name)
            elif action_lower == "switch":
                return SwitchWalletCommand(self._wallet_manager, name)

        return None
