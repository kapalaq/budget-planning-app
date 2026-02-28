"""Wallet Manager module to work with different wallets."""

from datetime import datetime
from typing import List, Optional

from models.category import CategoryManager
from models.recurrence_scheduler import RecurrenceScheduler
from models.transaction import TransactionType, Transfer
from strategies.sorting import WalletSortingContext
from wallet.wallet import Wallet


class WalletManager:
    """Wallet Manager class to work with different wallets."""

    def __init__(self):
        self._wallets: dict[str, Wallet] = {}
        self._current_wallet: Optional[Wallet] = None
        self._sorting_context = WalletSortingContext()
        self._category_manager = CategoryManager()
        self._recurrence_scheduler = RecurrenceScheduler(self)

    @property
    def sorting_context(self) -> WalletSortingContext:
        return self._sorting_context

    @property
    def current_wallet(self) -> Optional[Wallet]:
        return self._current_wallet

    @property
    def recurrence_scheduler(self) -> RecurrenceScheduler:
        return self._recurrence_scheduler

    def switch_wallet(self, name: str) -> bool:
        """Switch to a wallet by its name."""
        wallet = self._wallets.get(name)
        if wallet:
            self._current_wallet = wallet
            return True
        return False

    def get_sorted_wallets(self) -> List[Wallet]:
        """Get all wallets sorted by current strategy."""
        return self._sorting_context.sort(self._wallets.values())

    def wallet_count(self) -> int:
        """Return the number of wallets."""
        return len(self._wallets)

    def add_wallet(self, wallet: Wallet) -> bool:
        """Add a wallet to the list of wallets."""
        if self._wallets.get(wallet.name.lower(), None) is None:
            wallet.assign_category_manager(self._category_manager)
            self._wallets[wallet.name.lower()] = wallet
            # Set as current wallet if it's the first one
            if self._current_wallet is None:
                self._current_wallet = wallet
            return True
        return False

    def get_wallets(self) -> dict[str, Wallet]:
        """Get all wallets."""
        return self._wallets

    def get_wallet(self, name: str) -> Optional[Wallet]:
        """Get a wallet by its name."""
        return self._wallets.get(name.lower(), None)

    def remove_wallet(self, name: str) -> bool:
        """Remove a wallet by its name."""
        wallet_to_delete = self._wallets.get(name.lower())
        if wallet_to_delete is None:
            return False

        del self._wallets[name.lower()]

        # Remove recurring transactions for this wallet
        self._recurrence_scheduler.remove_recurring_for_wallet(name)

        # If we deleted the current wallet, switch to another or None
        if self._current_wallet and self._current_wallet.name.lower() == name:
            if self._wallets:
                self._current_wallet = next(iter(self._wallets.values()))
            else:
                self._current_wallet = None

        wallet_to_delete.delete()
        return True

    def update_wallet(
        self,
        old_name: str,
        new_name: str = None,
        currency: str = None,
        description: str = None,
    ) -> bool:
        """Update a wallet by its name."""
        wallet = self._wallets.get(old_name.lower())
        if wallet is None:
            return False

        # If renaming, check that new name doesn't already exist
        if new_name and new_name != old_name:
            if self._wallets.get(new_name.lower()) is not None:
                return False
            # Remove old key and add with new name
            del self._wallets[old_name.lower()]
            wallet.name = new_name
            self._wallets[new_name.lower()] = wallet

            # Update recurring transactions that reference this wallet
            for recurring in self._recurrence_scheduler.get_recurring_for_wallet(
                old_name
            ):
                recurring.wallet_name = new_name

        # Update other fields if provided
        if currency:
            wallet.currency = currency
        if description is not None:
            wallet.description = description

        return True

    def transfer(
        self,
        from_wallet_name: str,
        to_wallet_name: str,
        amount: float,
        description: str = "",
        datetime_created: datetime = None,
    ) -> bool:
        """Transfer money between two wallets.

        Creates synchronized Transfer transactions in both wallets:
        - Source wallet gets an expense Transfer (-amount)
        - Target wallet gets an income Transfer (+amount)

        Args:
            from_wallet_name: Name of the source wallet.
            to_wallet_name: Name of the target wallet.
            amount: Amount to transfer (positive value).
            description: Optional description for the transfer.
            datetime_created: Optional datetime for the transfer.

        Returns:
            True if transfer was successful, False otherwise.
        """
        from_wallet = self.get_wallet(from_wallet_name)
        to_wallet = self.get_wallet(to_wallet_name)

        if from_wallet is None or to_wallet is None:
            return False

        if from_wallet == to_wallet:
            return False

        if amount <= 0:
            return False

        if datetime_created is None:
            datetime_created = datetime.now()

        # Create the outgoing transfer (expense from source wallet)
        outgoing = Transfer(
            amount=amount,
            transaction_type=TransactionType.EXPENSE,
            category="Transfer",
            description=description,
            datetime_created=datetime_created,
            source=from_wallet,
        )

        # Create the incoming transfer (income to target wallet)
        incoming = Transfer(
            amount=amount,
            transaction_type=TransactionType.INCOME,
            category="Transfer",
            description=description,
            datetime_created=datetime_created,
            source=to_wallet,
        )

        # Link the transfers together
        outgoing.connected = incoming
        incoming.connected = outgoing

        # Add transfers to their respective wallets
        from_wallet.add_transaction(outgoing)
        to_wallet.add_transaction(incoming)

        return True
