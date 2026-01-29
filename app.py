"""Main application class for the budget planner."""
from models.category import CategoryManager
from wallet.wallet import Wallet
from wallet.wallet_manager import WalletManager
from commands.handlers import CommandFactory
from ui.display import Display
from ui.input_handler import InputHandler


class BudgetPlannerApp:
    """Main application class that orchestrates the budget planner."""

    def __init__(self):
        self._wallet_manager = WalletManager()
        # Create a default wallet
        default_wallet = Wallet(name="Main Wallet", currency="KZT")
        self._wallet_manager.add_wallet(default_wallet)
        self._command_factory = CommandFactory(self._wallet_manager)
        self._running = False

    def _show_welcome(self):
        """Display welcome message and initial dashboard."""
        print("\n" + "=" * 50)
        print("   Welcome to Budget Planner!")
        print("=" * 50)
        Display.show_help()
        current_wallet = self._wallet_manager.current_wallet
        if current_wallet:
            Display.show_dashboard(current_wallet)
        else:
            Display.show_info("No wallets yet. Use 'add_wallet' to create one.")

    def _process_input(self) -> bool:
        """Process user input and return whether to continue."""
        # Materialize any due recurring transactions
        scheduler = self._wallet_manager.recurrence_scheduler
        generated = scheduler.process_due_transactions()
        if generated > 0:
            Display.show_info(
                f"{generated} recurring transaction(s) generated"
            )

        command_str = InputHandler.get_command()
        command = self._command_factory.create_command(command_str)

        if command:
            return command.execute()
        else:
            Display.show_error(
                f"Unknown command: '{command_str}'. Type 'help' for available commands."
            )
            return True

    def run(self):
        """Run the main application loop."""
        self._running = True
        self._show_welcome()

        while self._running:
            try:
                self._running = self._process_input()
            except KeyboardInterrupt:
                print()
                Display.show_info("Use 'quit' to exit")
            except EOFError:
                self._running = False
                Display.show_info("Goodbye!")
