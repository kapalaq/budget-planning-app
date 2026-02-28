"""Main application class for the budget planner."""
import logging
from wallet.wallet import Wallet
from wallet.wallet_manager import WalletManager
from api.request_handler import RequestHandler
from ui.display import Display

logger = logging.getLogger(__name__)


class BudgetPlannerApp:
    """Main application class that orchestrates the budget planner."""

    def __init__(self):
        wallet_manager = WalletManager()
        # Create a default wallet
        default_wallet = Wallet(name="Main Wallet", currency="KZT")
        wallet_manager.add_wallet(default_wallet)

        handler = RequestHandler(wallet_manager)
        self._display = Display(handler)

    def run(self):
        """Run the main application loop."""
        logger.info("Application started")
        self._display.run()
