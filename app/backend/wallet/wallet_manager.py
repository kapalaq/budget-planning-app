"""Wallet Manager module to work with different wallets."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from models.category import CategoryManager
from models.recurrence_scheduler import RecurrenceScheduler
from models.transaction import TransactionType, Transfer
from strategies.sorting import WalletSortingContext
from wallet.wallet import DepositWallet, GoalStatus, Wallet, WalletType


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

    def from_json(self, data: Dict[str, Any]) -> "WalletManager":
        """Builds WalletManager class from persisted dict data."""
        if data is None:
            return self

        self._category_manager = CategoryManager().from_json(
            data.get("category_manager")
        )
        self._sorting_context = WalletSortingContext().from_json(
            data.get("sorting_context")
        )
        self._recurrence_scheduler = RecurrenceScheduler(self).from_json(
            data.get("recurrent_scheduler")
        )

        for wallet_data in data.get("wallets", []):
            w_type = wallet_data.get("wallet_type", "regular")
            if w_type == WalletType.DEPOSIT.value:
                wallet = DepositWallet.from_json(wallet_data)
            else:
                wallet = Wallet.from_json(wallet_data)

            if wallet.name == data.get("current_wallet"):
                self._current_wallet = wallet
            self.add_wallet(wallet)

        # Resolve Transfer connections across wallets
        self._resolve_transfer_links()

        return self

    def _resolve_transfer_links(self) -> None:
        """Wire up Transfer.source and Transfer.connected across all wallets."""
        # Build a global index: transaction id -> (Transfer, Wallet)
        index: Dict[str, tuple] = {}
        for wallet in self._wallets.values():
            for t in wallet._Wallet__transactions.values():
                if isinstance(t, Transfer):
                    t.source = wallet
                    index[t.id] = (t, wallet)

        # Resolve connected references
        for transfer, _ in index.values():
            pending_id = getattr(transfer, "_pending_connected_id", None)
            if pending_id and pending_id in index:
                transfer.connected = index[pending_id][0]
            if hasattr(transfer, "_pending_connected_id"):
                del transfer._pending_connected_id

    def to_json(self) -> Dict[str, Any]:
        """Turns WalletManager data into dict for persistance."""
        data = {}

        data["category_manager"] = self._category_manager.to_json()
        data["sorting_context"] = self._sorting_context.to_json()
        data["recurrent_scheduler"] = self._recurrence_scheduler.to_json()
        data["current_wallet"] = self._current_wallet.name
        data["wallets"] = [wallet.to_json() for wallet in self._wallets.values()]

        return data

    def switch_wallet(self, name: str) -> bool:
        """Switch to a wallet by its name."""
        wallet = self._wallets.get(name.lower())
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

    def remove_wallet(self, name: str, force: bool = False) -> bool:
        """Remove a wallet by its name."""
        wallet_to_delete = self._wallets.get(name.lower())
        if wallet_to_delete is None:
            return False

        if (
            not force
            and (wallet_to_delete.is_goal_wallet or wallet_to_delete.is_bill_wallet)
            and wallet_to_delete.goal_status == GoalStatus.ACTIVE
        ):
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
                if recurring.wallet_name.lower() == old_name.lower():
                    recurring.wallet_name = new_name
                if (
                    recurring.target_wallet_name
                    and recurring.target_wallet_name.lower() == old_name.lower()
                ):
                    recurring.target_wallet_name = new_name

        # Update other fields if provided
        if currency:
            wallet.currency = currency
        if description is not None:
            wallet.description = description

        return True

    # ── Goal helpers ───────────────────────────────────────────────────

    def get_active_goals(self) -> List[Wallet]:
        """Get all active savings goal wallets."""
        return [
            w
            for w in self._wallets.values()
            if w.is_goal_wallet and w.goal_status == GoalStatus.ACTIVE
        ]

    def get_completed_goals(self) -> List[Wallet]:
        """Get all completed savings goal wallets."""
        return [
            w
            for w in self._wallets.values()
            if w.is_goal_wallet and w.goal_status == GoalStatus.COMPLETED
        ]

    def get_all_goals(self) -> List[Wallet]:
        """Get all savings goal wallets (including hidden)."""
        return [w for w in self._wallets.values() if w.is_goal_wallet]

    def get_visible_wallets(self) -> List[Wallet]:
        """Get wallets visible on dashboard (non-goal/non-bill + active goals).

        Bills are always excluded from portfolio totals.
        """
        return [
            w
            for w in self._wallets.values()
            if not w.is_bill_wallet
            and (not w.is_goal_wallet or w.goal_status == GoalStatus.ACTIVE)
        ]

    def complete_goal(self, wallet_name: str) -> bool:
        """Mark a goal as completed."""
        wallet = self.get_wallet(wallet_name)
        if wallet is None or not wallet.is_goal_wallet:
            return False
        if wallet.goal_status != GoalStatus.ACTIVE:
            return False
        wallet.goal_status = GoalStatus.COMPLETED
        wallet.goal_completed_at = datetime.now()
        return True

    def hide_goal(self, wallet_name: str) -> bool:
        """Hide a completed goal from the main UI."""
        wallet = self.get_wallet(wallet_name)
        if wallet is None or not wallet.is_goal_wallet:
            return False
        wallet.goal_status = GoalStatus.HIDDEN
        return True

    def reactivate_goal(self, wallet_name: str) -> bool:
        """Reactivate a completed or hidden goal."""
        wallet = self.get_wallet(wallet_name)
        if wallet is None or not wallet.is_goal_wallet:
            return False
        if wallet.goal_status == GoalStatus.ACTIVE:
            return False
        wallet.goal_status = GoalStatus.ACTIVE
        wallet.goal_completed_at = None
        return True

    # ── Bill helpers ──────────────────────────────────────────────────

    def get_active_bills(self) -> List[Wallet]:
        """Get all active bill wallets."""
        return [
            w
            for w in self._wallets.values()
            if w.is_bill_wallet and w.goal_status == GoalStatus.ACTIVE
        ]

    def get_completed_bills(self) -> List[Wallet]:
        """Get all completed bill wallets."""
        return [
            w
            for w in self._wallets.values()
            if w.is_bill_wallet and w.goal_status == GoalStatus.COMPLETED
        ]

    def get_all_bills(self) -> List[Wallet]:
        """Get all bill wallets (including hidden)."""
        return [w for w in self._wallets.values() if w.is_bill_wallet]

    def complete_bill(self, wallet_name: str) -> bool:
        """Mark a bill as completed."""
        wallet = self.get_wallet(wallet_name)
        if wallet is None or not wallet.is_bill_wallet:
            return False
        if wallet.goal_status != GoalStatus.ACTIVE:
            return False
        wallet.goal_status = GoalStatus.COMPLETED
        wallet.goal_completed_at = datetime.now()
        return True

    def hide_bill(self, wallet_name: str) -> bool:
        """Hide a completed bill from the main UI."""
        wallet = self.get_wallet(wallet_name)
        if wallet is None or not wallet.is_bill_wallet:
            return False
        wallet.goal_status = GoalStatus.HIDDEN
        return True

    def reactivate_bill(self, wallet_name: str) -> bool:
        """Reactivate a completed or hidden bill."""
        wallet = self.get_wallet(wallet_name)
        if wallet is None or not wallet.is_bill_wallet:
            return False
        if wallet.goal_status == GoalStatus.ACTIVE:
            return False
        wallet.goal_status = GoalStatus.ACTIVE
        wallet.goal_completed_at = None
        return True

    def transfer(
        self,
        from_wallet_name: str,
        to_wallet_name: str,
        amount: float,
        description: str = "",
        datetime_created: datetime = None,
        received_amount: float = None,
    ) -> bool:
        """Transfer money between two wallets.

        Creates synchronized Transfer transactions in both wallets:
        - Source wallet gets an expense Transfer (-amount)
        - Target wallet gets an income Transfer (+received_amount or +amount)

        Args:
            from_wallet_name: Name of the source wallet.
            to_wallet_name: Name of the target wallet.
            amount: Amount to transfer (positive value, in source currency).
            description: Optional description for the transfer.
            datetime_created: Optional datetime for the transfer.
            received_amount: Amount received in target currency. If None,
                uses the same amount (same-currency transfer).

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

        incoming_amount = received_amount if received_amount is not None else amount

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
            amount=incoming_amount,
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
